# Assumptions:
# All USA data
# No need to prompt the user to fix "bad" values
# What constitutes a "correct value"? Right now we're assuming a correct value is a value that is not bad and not incorrect formatting.
# We're assuming a phone number is formatted as (123) 456-7890
# not sure what would constitute an incorrectly formatted email...

import itertools
import json
import numpy as np
import os
import pandas as pd
import re
import sys

# load dictionary of all valid state names and their two letter code
with open('states.json', 'r') as state_file:
    state_codes = json.load(state_file)

# all available zip codes for each state...from: https://www.zipcodestogo.com
with open('additional_state_code_data.json', 'r') as zip_file:
    adtl_zip_data = json.load(zip_file)

# this list is used to assist with quickly finding out if a zip code is valid from the adtl_zip_data dict
all_adtl_zips = list(itertools.chain.from_iterable(adtl_zip_data.values()))

email_regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

def main(options):
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

    num_missing_soc_secs, num_missing_states, num_missing_zips, num_missing_phones, num_missing_emails = \
        find_missing_values(user_data)

    # cycle through all records to find bad, incorrect formatted (and fix), and correct values
    num_correct_soc_secs = 0
    num_correct_states = 0
    num_correct_zips = 0
    num_correct_phones = 0
    num_correct_emails = 0

    for a in range(user_data.shape[0]):

        correct_soc_sec = validate_social_security(user_data, a)      
        correct_state = validate_state(user_data, a)
        correct_zip = validate_zip(user_data, a)
        correct_phone = validate_phone(user_data, a)
        correct_email = validate_email(user_data, a)

        state_and_zip_validation(user_data, a)

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

    user_data.to_csv(os.path.join(options.output_path, 'new_data_quality_case_study.csv'), index=False)

def validate_social_security(user_data, a):
    if not pd.isnull(user_data['social_security'][a]):
        # bad value
        if not ((user_data['social_security'][a].replace('-','')).isnumeric() and len(user_data['social_security'][a].replace('-','')) == 9):
            print('INVALID SOCIAL SECURITY NUMBER. value: {} on index: {}'.format(user_data['social_security'][a], a))
            return False
            
        # incorrect formatting
        i = user_data['social_security'][a]
        if ((i.isnumeric() and len(i) == 9)):
            user_data.at[a, 'social_security'] = i[0:3] + '-' + i[3:5] + '-' + i[5:]
            return False

    return True 

def validate_state(user_data, a):
    correct_state = True
    if not pd.isnull(user_data['state'][a]):
        # bad value
        if (not user_data['state'][a] in state_codes.keys()) and (not user_data['state'][a] in state_codes.values()):
            print('INVALID STATE. value: {} on index: {}'.format(user_data['state'][a], a))
            correct_state = False

        # incorrect formatting
        i = user_data['state'][a]
        if (i not in state_codes.values()):
            # check if i is a valid state
            if i.lower().capitalize() in state_codes.keys(): # make sure to format the state correctly when searching
                user_data.at[a, 'state'] = state_codes[i.lower().capitalize()]
            correct_state = False

    return correct_state

def validate_zip(user_data, a):
    if not pd.isnull(user_data['zip'][a]):
        # bad value
        if not (user_data['zip'][a] in all_adtl_zips):
            print('INVALID ZIP CODE. value: {} on index: {}'.format(user_data['zip'][a],a))
            return False

    return True

def validate_phone(user_data, a):
    # bad values are complicated. If the phone number has 11 digits, and the first is 1,
    # is that a valid phone number with a USA prefix or an invalid number?

    # incorrect formatting
    correct_phone = True
    if not pd.isnull(user_data['phone1'][a]):
        i = user_data['phone1'][a]
        if i[:2] == '+1': # it's already assumed we're in USA
            correct_phone = False
            i = i[2:].strip()
        # phone format (123) 456-7890
        #if not ( \
        #    (len(i) == 14) and \
        #    i[0] == '(' and \
        #    i[1:4].isnumeric() and \
        #    i[4] == ')' and \
        #    i[5] == ' ' and \
        #    i[6:9].isnumeric() and \
        #    i[9] == '-' and \
        #    i[10:].isnumeric() \
        #    ):
        #    correct_phone = False
        #temp_phone = [p for p in user_data['phone1'][a] if p.isnumeric()]
        #temp_phone = ''.join(temp_phone)
        #if len(temp_phone) == 10:
        #    i = '({}) {}-{}'.format(temp_phone[0:3], temp_phone[3:6], temp_phone[6:])
        #    user_data.at[a, 'phone1'] = i

        # phone format 123-456-7890
        if not ( \
            (len(i) == 12) and \
            i[0:3].isnumeric() and \
            i[3] == '-' and \
            i[4:7].isnumeric() and \
            i[7] == '-' and \
            i[8:].isnumeric()
            ):
            correct_phone = False
        temp_phone = [p for p in user_data['phone1'][a] if p.isnumeric()]
        temp_phone = ''.join(temp_phone)
        if len(temp_phone) == 10:
            i = '{}-{}-{}'.format(temp_phone[0:3], temp_phone[3:6], temp_phone[6:])
            user_data.at[a, 'phone1'] = i

    return correct_phone

def validate_email(user_data, a):
    if not pd.isnull(user_data['email'][a]):
        # bad value
        if(not re.search(email_regex, user_data['email'][a])):
            print('INVALID EMAIL ADDRESS. email: {}, index: {}'.format(user_data['email'][a], a))
            return False

    return True

def state_and_zip_validation(user_data, a):
    # another layer of validation for zip codes will be to match it up with the state.
    # if the validation data does not match for the zip and state, then it's going to require manual inspection.
    if not (pd.isnull(user_data['state'][a]) or pd.isnull(user_data['zip'][a])):
        # for each record's state, make sure its zip code belongs to that state
        if user_data['zip'][a] in all_adtl_zips:
            state_code = ''
            if user_data['state'][a] in state_codes.values():
                state_code = user_data['state'][a]
            elif user_data['state'][a] in state_codes.keys():
                state_code = state_codes[user_data['state'][a]]

            if state_code != '':
            # check that the value isn't in the adtl_zip_data 
                if not (user_data['zip'][a] in adtl_zip_data[state_code]):
                    print('ZIP CODE AND STATE DO NOT MATCH ERROR. state: {}, zip: {}, index: {}'.format(user_data['state'][a], user_data['zip'][a], a))

def find_missing_values(user_data):
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
    
    num_missing_soc_secs = len(soc_secs_missing_indexes)
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

    return num_missing_soc_secs, num_missing_states, num_missing_zips, num_missing_phones, num_missing_emails

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