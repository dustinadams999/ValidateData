# TODO: organize finding missing and correct values, bad data, and formatting into functions

# Questions:
# Can we safely assume this is all USA data? Seems to be the case.
# Should we write the data that needs to be manually checked back to the csv file?
# Or should we prompt the user?
# What constitutes a "correct value"? Right now we're assuming a correct value is a value that is not bad and not incorrect formatting.

# We're assuming a phone number is formatted as (123) 456-7890

import itertools
import json
import numpy as np
import os
import pandas as pd
import re
import sys
from IPython import embed as shell

def main(options):
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

    # data provided by Data Governance
    try:
        csv_dtype = {
            'social_security':  str,
            'state':            str,
            'zip':              str,
            'phone1':           str,
            'email':            str
        }
        user_data = pd.read_csv(options.input_file, dtype=csv_dtype)
    except:
        print('Error reading csv file. Check path to make sure it is a valid csv file')
        exit(1)

    # data provided by https://simplemaps.com/data/us-zips
    zip_data = pd.read_csv('/Users/dustinadams/quicken_code_test/simplemaps_uszips_basicv1.77/uszips.csv')

    # the above data set is not complete (has some missing zip codes) - also need to grab from this site https://www.zipcodestogo.com
    with open('additional_state_code_data.json', 'r') as zip_file:
        adtl_zip_data = json.load(zip_file)

    # this list is used to assist with quickly finding out if a zip code is valid from the adtl_zip_data dict
    all_adtl_zips = list(itertools.chain.from_iterable(adtl_zip_data.values()))

    # load dictionary of all valid state names and their two letter code
    with open('states.json', 'r') as state_file:
        state_codes = json.load(state_file)

    # identify and count missing values
    soc_secs_missing_indexes = []
    states_missing_indexes = []
    zips_missing_indexes = []
    phones_missing_indexes = []
    emails_missing_indexes = []

    for a in range(user_data.shape[0]):
        if pd.isnull(user_data['social_security'][a]): soc_secs_missing_indexes.append(a)
        if pd.isnull(user_data['state'][a]): states_missing_indexes.append(a)
        if pd.isnull(user_data['zip'][a]): zips_missing_indexes.append(a)
        if pd.isnull(user_data['phone1'][a]): phones_missing_indexes.append(a)
        if pd.isnull(user_data['email'][a]): emails_missing_indexes.append(a)
    
    num_missing_soc_secs = len(soc_secs_missing_indexes) # TODO: change to length of the array
    num_missing_states = len(states_missing_indexes)
    num_missing_zips = len(zips_missing_indexes)
    num_missing_phones = len(phones_missing_indexes)
    num_missing_emails = len(emails_missing_indexes)

    print('Number of missing social security numbers: {}'.format(num_missing_soc_secs))
    print('Indexes of missing social security numbers: {}\n'.format(soc_secs_missing_indexes))
    print('Number of missing states: {}'.format(num_missing_states))
    print('Indexes of missing states: {}\n'.format(states_missing_indexes))
    print('Number of missing zip codes: {}'.format(num_missing_zips))
    print('Indexes of missing zip codes: {}\n'.format(zips_missing_indexes))
    print('Number of missing phones: {}'.format(num_missing_phones))
    print('Indexes of missing phones: {}\n'.format(phones_missing_indexes))
    print('Number of missing email addresses: {}'.format(num_missing_emails))
    print('Indexes of missing email addresses: {}\n'.format(emails_missing_indexes))

    # cycle through all records to find bad, incorrect formatted (and fix), and correct values
    num_correct_soc_secs = 0
    num_correct_states = 0
    num_correct_zips = 0
    num_correct_phones = 0
    num_correct_emails = 0

    for a in range(user_data.shape[0]):
        correct_soc_sec = True
        correct_state = True
        correct_zip = True
        correct_phone = True
        correct_email = True

        # social security: if the value is not XXX-XX-XXXX, and the value is not 9 ints, it's a bad value
        if not pd.isnull(user_data['social_security'][a]):
            # bad value
            if not ((user_data['social_security'][a].replace('-','')).isnumeric() and len(user_data['social_security'][a].replace('-','')) == 9):
                correct_soc_sec = False
                print('INVALID SOCIAL SECURITY NUMBER. value: {} on index: {}'.format(user_data['social_security'][a], a))

            # incorrect formatting
            i = user_data['social_security'][a]
            if ((i.isnumeric() and len(i) == 9)):
                correct_soc_sec = False
                user_data.at[a, 'social_security'] = i[0:3] + '-' + i[3:5] + '-' + i[5:]

        # state: If neither the state nor the 2 letter state code exists, then it's a bad value
        if not pd.isnull(user_data['state'][a]):
            # bad value
            if (not user_data['state'][a] in state_codes.keys()) and (not user_data['state'][a] in state_codes.values()):
                correct_state = False
                print('INVALID STATE. value: {} on index: {}'.format(user_data['state'][a], a))

            # incorrect formatting
            i = user_data['state'][a]
            if (i not in state_codes.values()):
                correct_state = False
                # check if i is a valid state
                if i.lower().capitalize() in state_codes.keys(): # make sure to format the state correctly when searching
                    user_data.at[a, 'state'] = state_codes[i.lower().capitalize()]


        # find invalid zip codes - if the zip code converted to an int does not exist, then it's a bad value
        if not pd.isnull(user_data['zip'][a]):
            # bad value
            if not (user_data['zip'][a] in all_adtl_zips):
                correct_zip = False
                print('INVALID ZIP CODE. value: {} on index: {}'.format(user_data['zip'][a],a))

            # incorrect formatting
            # phone (123) 456-7890
            # TODO: comment out a few different formatting possibilities so we can switch between,
            # such as (123)456-7890 and 123-456-7890
            i = user_data['phone1'][a]
            if i[:2] == '+1': # it's already assumed we're in USA
                correct_phone = False
                i = i[2:].strip()
            if (len(i) != 14) or (not (i[1:4]+i[6:9]+i[10:]).isnumeric()):
                correct_phone = False
            if len(i.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')) == 10:
                i = i.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
                i = '({}) {}-{}'.format(i[0:3], i[3:6], i[6:])
                user_data.at[a, 'phone1'] = i

        if not pd.isnull(user_data['email'][a]):
            # bad value
            if(not re.search(regex, user_data['email'][a])):
                correct_email = False
                print('INVALID EMAIL ADDRESS. email: {}, index: {}'.format(user_data['email'][a], a))

        # another layer of validation for zip codes will be to match it up with the state.
        # if the validation data does not match for the zip and state, then it's going to require manual inspection.
        # TODO: we don't actually need the csv file - just use the json file
        if not (pd.isnull(user_data['state'][a]) or pd.isnull(user_data['zip'][a])):
            # for each record's state, make sure its zip code belongs to that state
            state_code = ''
            if user_data['state'][a] in state_codes.values():
                state_code = user_data['state'][a]
            elif user_data['state'][a] in state_codes.keys():
                state_code = state_codes[user_data['state'][a]]

            if state_code != '':
            # check that the value isn't in the adtl_zip_data 
                if not (user_data['zip'][a] in adtl_zip_data[state_code]):
                    # get index of the zip code from the zip_data dataframe
                    zip_index = (zip_data['zip'][zip_data['zip'] == int(user_data['zip'][a])]).index[0]
                    if zip_data['state_id'][zip_index] != state_code:
                        print('ZIP CODE AND STATE DO NOT MATCH ERROR. state: {}, zip: {}, index: {}'.format(user_data['state'][a], user_data['zip'][a], a))

        # not sure what would constitute an incorrectly formatted email...

        if correct_soc_sec: num_correct_soc_secs += 1
        if correct_state: num_correct_states += 1
        if correct_zip: num_correct_zips +=1
        if correct_phone: num_correct_phones += 1
        if correct_email: num_correct_emails += 1

    print('Correct social security numbers: {}'.format(num_correct_soc_secs - num_missing_soc_secs))
    print('Correct states: {}'.format(num_correct_states - num_missing_states))
    print('Correct zip codes: {}'.format(num_correct_zips - num_missing_zips))
    print('Correct phone numbers: {}'.format(num_correct_phones - num_missing_phones))
    print('Correct email addresses: {}'.format(num_correct_emails - num_missing_emails))


    # TODO: Create functions for each check
    # TODO: add the path that was entered by the user for the below file

    user_data.to_csv('new_data_quality_case_study.csv', index=False)

if __name__ == '__main__':
    from optparse import OptionParser

    usage = 'usage: %prog -i csv-input-file -o output-directory'
    parser = OptionParser(usage)

    parser.add_option('-i', '--input-file', dest='input_file', action='store', default='data_quality_case_study.csv', help='Input path')
    parser.add_option('-o', '--output-path', dest='output_path', action='store', default=os.getcwd(), help='Output path for cleaned csv file')

    (options, args) = parser.parse_args()

    if not os.path.isfile(options.input_file):
        parser.error('input file given by -i option does not exist.')
    if not os.path.isdir(options.output_path):
        parser.error('output path given by -o option does not exist.')

    main(options)