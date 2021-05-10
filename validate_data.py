# TODO: organize finding missing and correct values, bad data, and formatting into functions

# Questions:
# Can we safely assume this is all USA data? Seems to be the case.
# Should we write the data that needs to be manually checked back to the csv file?
# Or should we prompt the user?

import itertools
import json
import numpy as np
import os
import pandas as pd
import re
import sys
from IPython import embed as shell

def main(options):
    # data provided by Data Governance
    try:
        #user_data = pd.read_csv('data_quality_case_study.csv')
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
    num_empty_soc_secs = user_data.isnull().sum()[0]
    num_empty_states = user_data.isnull().sum()[1]
    num_empty_zips = user_data.isnull().sum()[2]
    num_empty_phones = user_data.isnull().sum()[3]
    num_empty_emails = user_data.isnull().sum()[4]
    print('Number of missing social security numbers: {}'.format(num_empty_soc_secs))
    print('Number of missing states: {}'.format(num_empty_soc_secs))
    print('Number of missing zip codes: {}'.format(num_empty_soc_secs))
    print('Number of missing phone numbers: {}'.format(num_empty_soc_secs))
    print('Number of missing email addresses: {}'.format(num_empty_soc_secs))

    # TODO: identify and count correct values (of all columns)

    # *************************
    # CHECKING FOR BAD VALUES *
    # *************************

    # TODO: combine all the for loops into one

    # social security: if the value is not XXX-XX-XXXX, and the value is not 9 ints, it's a bad value
    a = 0
    for i in user_data['social_security']:
        try:
            if not ((i.replace('-','')).isnumeric() and len(i.replace('-','')) == 9):
                raise Error()
        except:
                print('SOCIAL SECURITY ERROR. value: {} on index: {}'.format(i, a))
        a += 1

    # state: If neither the state nor the 2 letter state code exists, then it's a bad value
    a = 0
    for i in user_data['state']:
        if (not i in state_codes.keys()) and (not i in state_codes.values()):
            print('STATE ERROR. value: {} on index: {}'.format(i, a))
        a += 1

    # phone: If the formatting is not (XXX) XXX-XXXX (or XXX-XXX-XXXX or XXXXXXXXXX) then it's bad 

    # find invalid zip codes - if the zip code converted to an int does not exist, then it's a bad value
    a = 0
    for i in user_data['zip']:
        try:
            #if not int(i) in zip_data['zip'].values:
            #shell()
            if not str(int(i)) in all_adtl_zips:
                raise Error()
        except:
            print('ZIP ERROR. value: {} on index: {}'.format(i,a))
        a += 1

    # another layer of validation for zip codes will be to match it up with the state.
    # if the validation data does not match for the zip and state, then it's going to require manual inspection.
    a = 0
    for i in user_data['state']:
        if pd.isnull(user_data['state'][a]) or pd.isnull(user_data['zip'][a]):
            continue
        # for each record's state, make sure its zip code belongs to that state
        state_code = ''
        if i in state_codes.values():
            state_code = i
        elif i in state_codes.keys():
            state_code = state_codes[i]
        else:
            a += 1
            continue # it's already determined which records don't have valid states

        # check that the value isn't in the adtl_zip_data 
        if not (str(int(user_data['zip'][a])) in adtl_zip_data[state_code]):
            # get index of the zip code from the zip_data dataframe
            zip_index = (zip_data['zip'][zip_data['zip'] == int(user_data['zip'][a])]).index[0]
            if zip_data['state_id'][zip_index] != state_code:
                shell()
                print('ZIP CODE AND STATE DO NOT MATCH ERROR. state: {}, zip: {}, index: {}'.format(user_data['state'][a], user_data['zip'][a], a))
        a += 1

    # email: if the value is not $string@$string.$domain then it's a bad value
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    a = 0
    for i in user_data['email']:
        if pd.isnull(i):
            print('INVALID EMAIL ERROR. email: {}, index: {}'.format(i, a))
            a += 1
            continue
        try:
            if(not re.search(regex, i)):
                print('INVALID EMAIL ERROR. email: {}, index: {}'.format(i, a))
        except:
            shell()
        a += 1


    # ***********************************
    # CHECKING FOR INCORRECT FORMATTING *
    # ***********************************

    print('FIXING FORMATTING')

    # social security: if the value is not XXX-XX-XXXX (with dashes) and is 9 ints, add the dashes to the 9 ints
    a = 0
    for i in user_data['social_security']:
        if pd.isnull(i):
            a += 1
            continue
        if ((i.isnumeric() and len(i) == 9)):
            user_data.at[a, 'social_security'] = i[0:3] + '-' + i[3:5] + '-' + i[5:]
        a += 1    


    # state: if it's not the two letter state code, assume it's the full state name and rename it to the 2 letter code
    a = 0
    for i in user_data['state']:
        if pd.isnull(i):
            a += 1
            continue
        if (i not in state_codes.values()):
            # check if i is a valid state
            if i.lower().capitalize() in state_codes.keys(): # make sure to format the state correctly when searching
                user_data.at[a, 'state'] = state_codes[i.lower().capitalize()]
            #user_data.at[a, 'social_security'] = i[0:3] + '-' + i[3:5] + '-' + i[5:]
        a += 1 


    # zip: if it's any other data type not an int, change it to an int

    # phone: should be (XXX) XXX-XXXX, so if it's not then convert the 10 numbers to that.
    # if there's a +1 at the beginning, get rid of it.
    a = 0
    for i in user_data['phone1']:
        if pd.isnull(i):
            a +=1
            continue
        if i[:2] == '+1': # it's assumed we're in USA
            i = i[2:].strip()
        if len(i.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')) == 10:
            i = i.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
            i = '({}) {}-{}'.format(i[0:3], i[3:6], i[6:])
            user_data.at[a, 'phone1'] = i
        a += 1


    # TODO: Finally, produce the 'cleaned' dataset back
    user_data.to_csv('new_data_quality_case_study.csv', index=False)

    # TODO: Make a list of all the assumptions that we're making here:
    # ASSUMPTION: we're only working with USA data (this has implications for state, phone number, and zip)


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