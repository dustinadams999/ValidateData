"""
This program reads a set of csv data (encoded with columns social_security, state, zip, phone1, email),
determines and counts which values are correct, which require manual inspection, which have incorrect
formatting (and fixes the formatting), and writes to a new csv file.

Author: Dustin Adams
Date: May 8, 2021

Assumptions being made about the data:
All USA data
No need to prompt the user to fix "bad" values
A correct value is a value that is not bad and not incorrect formatting.
The zip codes column are encoded as integers (so there could be a leading 0 that is not shown).
A missing value is one that is null or equal to na or n/a (or some form of upper-case, lower-case mixture).

A correct social security number is formatted as 123-45-6789.
A correct state is formatted as two upper case letters, which correspond to an existing state code.
A correct zip code is a 5 digit integer that is an existing zip code...an incorrectly formatted zip is a 4 digit zip code that begins with 0 but was left off.
A phone number is formatted as 123-456-7890 (also capability for (123) 456-7890)
A correct email address is ${string}@${string}.${string}
"""

import itertools
import json
import numpy as np
import os
import pandas as pd
import re
import sys
from IPython import embed as shell

# load dictionary of all valid state names and their two letter code
with open('states.json', 'r') as state_file:
    state_codes = json.load(state_file)

# all available zip codes for each state...from: https://www.zipcodestogo.com
with open('additional_state_code_data.json', 'r') as zip_file:
    adtl_zip_data = json.load(zip_file)

# this list is used to assist with quickly finding out if a zip code is valid from the adtl_zip_data dict
all_adtl_zips = list(itertools.chain.from_iterable(adtl_zip_data.values()))

email_regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

# social security numbers should be unique
unique_soc_secs = []

def main(options):
    """
    Initialize dataframe, count missing values, determine correct values, bad values, and incorrect
    formatting (and fix). Display results to user.
    """
    # initialize pandas dataframe from csv file
    try:
        csv_dtype = {
            'social_security':  str,
            'state':            str,
            'zip':              str,
            'phone1':           str,
            'email':            str
        }
        user_data = pd.read_csv(options.input_file, dtype=csv_dtype)
        print('Reading file: {}\n'.format(os.path.abspath(options.input_file)))
    except:
        print('Error reading csv file. Check path to make sure it is a valid csv file')
        exit(1)

    # determine how many missing values are the dataframe
    num_missing_soc_secs, num_missing_states, num_missing_zips, num_missing_phones, num_missing_emails = \
        find_missing_values(user_data)

    print( \
        'Determining bad values and incorrect formatting. Bad values will be alerted, while '
        'incorrect formatting will not. Incorrect formatting will be automatically fixed.\n' \
        )

    num_correct_soc_secs = 0
    num_correct_states = 0
    num_correct_zips = 0
    num_correct_phones = 0
    num_correct_emails = 0

    # cycle through all records to find bad, incorrect formatted (and fix), and correct values
    for a in range(user_data.shape[0]):

        # determine if each column of the row are bad or incorrectly formatted
        correct_soc_sec = validate_social_security(user_data, a)      
        correct_state = validate_state(user_data, a)
        correct_zip = validate_zip(user_data, a)
        correct_phone = validate_phone(user_data, a)
        correct_email = validate_email(user_data, a)

        # determine if the state matches the zip code
        state_and_zip_validation(user_data, a)

        if correct_soc_sec: num_correct_soc_secs += 1
        if correct_state: num_correct_states += 1
        if correct_zip: num_correct_zips +=1
        if correct_phone: num_correct_phones += 1
        if correct_email: num_correct_emails += 1

    # Report findings to user
    print('\nCorrect social security numbers: {}'.format(num_correct_soc_secs - num_missing_soc_secs))
    print('Correct states: {}'.format(num_correct_states - num_missing_states))
    print('Correct zip codes: {}'.format(num_correct_zips - num_missing_zips))
    print('Correct phone numbers: {}'.format(num_correct_phones - num_missing_phones))
    print('Correct email addresses: {}\n'.format(num_correct_emails - num_missing_emails))

    print('Writing to file: {}'.format(os.path.abspath(os.path.join(options.output_path, 'new_data_quality_case_study.csv'))))
    user_data.to_csv(os.path.join(options.output_path, 'new_data_quality_case_study.csv'), index=False)

def validate_social_security(user_data, a):
    """
    This function checks an individual social security number, determines if it's a bad value,
    and if so alerts the user, as well as determines if the formatting is wrong. If the formatting
    is wrong, the user is not alerted, it is just fixed in the dataframe.
    123-45-6789
    """
    correct_soc_sec = True
    if not (pd.isnull(user_data['social_security'][a]) or \
        user_data['social_security'][a].lower() == 'na' or \
        user_data['social_security'][a].lower() == 'n/a'
        ):
        # check for bad value
        if not ((user_data['social_security'][a].replace('-','')).isnumeric() and len(user_data['social_security'][a].replace('-','')) == 9):
            print('INVALID SOCIAL SECURITY NUMBER. value: {} on index: {}'.format(user_data['social_security'][a], a))
            correct_soc_sec = False
            
        just_numbers = [s for s in user_data['social_security'][a] if s.isnumeric()]
        just_numbers = ''.join(just_numbers)

        if just_numbers in unique_soc_secs:
            print('DUPLICATE SOCIAL SECURITY NUMBER. value: {} on index: {}'.format(user_data['social_security'][a], a))
            correct_soc_sec = False
        else:
            unique_soc_secs.append(just_numbers)

        # check for incorrect formatting
        i = user_data['social_security'][a]
        if ((i.isnumeric() and len(i) == 9)):
            user_data.at[a, 'social_security'] = i[0:3] + '-' + i[3:5] + '-' + i[5:]
            correct_soc_sec = False

    return correct_soc_sec 

def validate_state(user_data, a):
    """
    This function checks an individual state, determines if it's a bad value,
    and if so alerts the user, as well as determines if the formatting is wrong. If the formatting
    is wrong, the user is not alerted, it is just fixed in the dataframe.
    """
    correct_state = True
    if not (pd.isnull(user_data['state'][a]) or \
        user_data['state'][a].lower() == 'na' or \
        user_data['state'][a].lower() == 'n/a'
        ):
        # check for bad value
        if (not user_data['state'][a] in state_codes.keys()) and (not user_data['state'][a] in state_codes.values()):
            print('INVALID STATE. value: {} on index: {}'.format(user_data['state'][a], a))
            correct_state = False

        # check for incorrect formatting
        i = user_data['state'][a]
        if (i not in state_codes.values()):
            # Check if both letters of the state code are not upper case
            if i.upper() in state_codes.values():
                user_data.at[a, 'state'] = state_codes[i.upper()]
            # check if i is a valid state
            elif i.lower().title() in state_codes.keys(): # make sure to format the state correctly when searching
                user_data.at[a, 'state'] = state_codes[i.lower().title()]
            correct_state = False

    return correct_state

def validate_zip(user_data, a):
    """
    This function checks an individual zip code, determines if it's a bad value,
    and if so alerts the user. No formatting is currently being checked on the zip code.
    """
    correct_zip = True
    if not (pd.isnull(user_data['zip'][a]) or \
        user_data['zip'][a].lower() == 'na' or \
        user_data['zip'][a].lower() == 'n/a'
        ):
        # if the zip code is length 4, check if appending a zero to the front makes it valid
        if len(user_data['zip'][a]) == 4:
            i = '0' + user_data['zip'][a]
        else:
            i = user_data['zip'][a]
        # check for incorrect formatting
        if (i in all_adtl_zips) and (not user_data['zip'][a] in all_adtl_zips):
            user_data.at[a, 'zip'] = i
            correct_zip = False
        # check for bad value
        elif not i in all_adtl_zips:
            print('INVALID ZIP CODE. value: {} on index: {}'.format(user_data['zip'][a],a))
            correct_zip = False

    return correct_zip

def validate_phone(user_data, a):
    """
    This function checks an individual phone number, determines if the formatting is wrong. If the formatting
    is wrong, the user is not alerted, it is just fixed in the dataframe.
    """
    correct_phone = True

    if not (pd.isnull(user_data['phone1'][a]) or \
        user_data['phone1'][a].lower() == 'na' or \
        user_data['phone1'][a].lower() == 'n/a'
        ):
        # Bad values here are a little complicated. If the phone number has 11 digits, and the first is 1,
        # we won't consider it bad, but everything outside of that is bad.
        temp_phone = [p for p in user_data['phone1'][a] if p.isnumeric()]
        temp_phone = ''.join(temp_phone) # we just want the digits
        if temp_phone[0] == '1' and len(temp_phone) == 11: # it's already assumed we're in USA
            temp_phone = temp_phone[1:]

        # only '+', ' ', '-', '(', ')' characters allowed in the phone number
        valid_chars = True
        tmp_valid = user_data['phone1'][a].replace(' ', '').replace('+', '').replace('-', '').replace(')', '').replace('(', '')
        for t in tmp_valid:
            if not t.isnumeric():
                valid_chars = False

        if not ((len(temp_phone) == 10) and (valid_chars)):
            print('INVALID PHONE NUMBER. value: {} on index: {}'.format(user_data['phone1'][a],a))
            correct_phone = False

        # check for incorrect formatting on (123) 456-7890
        #i = user_data['phone1'][a]
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

        #if len(temp_phone) == 10:
        #    i = '({}) {}-{}'.format(temp_phone[0:3], temp_phone[3:6], temp_phone[6:])
        #    user_data.at[a, 'phone1'] = i

        # check for incorrect formatting on 123-456-7890
        # From the North American Numbering Plan
        i = user_data['phone1'][a]
        if not ( \
            (len(i) == 12) and \
            i[0:3].isnumeric() and \
            i[3] == '-' and \
            i[4:7].isnumeric() and \
            i[7] == '-' and \
            i[8:].isnumeric()
            ):
            correct_phone = False

        if len(temp_phone) == 10:
            i = '{}-{}-{}'.format(temp_phone[0:3], temp_phone[3:6], temp_phone[6:])
            user_data.at[a, 'phone1'] = i


    return correct_phone

def validate_email(user_data, a):
    """
    This function checks an individual email address, determines if it's a bad value,
    and if so alerts the user. No formatting is currently being checked on the email address.
    """
    if not (pd.isnull(user_data['email'][a]) or \
        user_data['email'][a].lower() == 'na' or \
        user_data['email'][a].lower() == 'n/a'
        ):
        # check for bad value
        if(not re.search(email_regex, user_data['email'][a])):
            print('INVALID EMAIL ADDRESS. email: {}, index: {}'.format(user_data['email'][a], a))
            return False

    return True

def state_and_zip_validation(user_data, a):
    """
    This function checks another layer of validation: whether zip codes match up with the state.
    If the validation data does not match for the zip and state, then it's a bad value for
    the state and zip.
    """
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
    """
    This function identifies and counts missing values in the dataframe.
    """
    soc_secs_missing_indexes = []
    states_missing_indexes = []
    zips_missing_indexes = []
    phones_missing_indexes = []
    emails_missing_indexes = []

    for a in range(user_data.shape[0]):
        if pd.isnull(user_data['social_security'][a]) or \
            (user_data['social_security'][a].lower() == 'na') or \
            (user_data['social_security'][a].lower() == 'n/a'):
            soc_secs_missing_indexes.append(a)
        if pd.isnull(user_data['state'][a]) or \
            (user_data['state'][a].lower() == 'na') or \
            (user_data['state'][a].lower() == 'n/a'):
            states_missing_indexes.append(a)
        if pd.isnull(user_data['zip'][a]) or \
            (user_data['zip'][a].lower() == 'na') or \
            (user_data['zip'][a].lower() == 'n/a'):
            zips_missing_indexes.append(a)
        if pd.isnull(user_data['phone1'][a]) or \
            (user_data['phone1'][a].lower() == 'na') or \
            (user_data['phone1'][a].lower() == 'n/a'):
            phones_missing_indexes.append(a)
        if pd.isnull(user_data['email'][a]) or \
            (user_data['email'][a].lower() == 'na') or \
            (user_data['email'][a].lower() == 'n/a'): 
            emails_missing_indexes.append(a)
    
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

    # -p option for phone formatting 123-456-7890, default is (123) 456-7890

    (options, args) = parser.parse_args()

    if not os.path.isfile(options.input_file):
        parser.error('input file given by -i option does not exist.')
    if not os.path.isdir(options.output_path):
        parser.error('output path given by -o option does not exist.')

    main(options)