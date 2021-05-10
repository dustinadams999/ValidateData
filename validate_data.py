# TODO: setup commandline arguments
# TODO: setup main and other functions
# TODO: try to decide what to do about dependency requirements

# Questions: Can we safely assume this is all USA data? Seems to be the case.

import json
import numpy as np
import pandas as pd
import sys
from IPython import embed as shell

def main():
  # data provided by Data Governance
  user_data = pd.read_csv('data_quality_case_study.csv')

  # data provided by https://simplemaps.com/data/us-zips
  zip_data = pd.read_csv('/Users/dustinadams/quicken_code_test/simplemaps_uszips_basicv1.77/uszips.csv')

  # the above data set is not complete - also need to grab from this site https://www.zipcodestogo.com
  with open('additional_state_code_data.json', 'r') as zip_file:
    adtl_zip_data = json.load(zip_file)

  all_adtl_zips = []
  for key in adtl_zip_data:
    all_adtl_zips += adtl_zip_data[key]

  # load dictionary of all valid state names and their two letter code
  with open('states.json', 'r') as state_file:
    state_codes = json.load(state_file)

  # identify and count missing values
  # TODO: currently we're only counting, we also need to identify (by index)
  num_empty_soc_secs = user_data.isnull().sum()[0]
  num_empty_states = user_data.isnull().sum()[1]
  num_empty_zips = user_data.isnull().sum()[2]
  num_empty_phones = user_data.isnull().sum()[3]
  num_empty_emails = user_data.isnull().sum()[4]

  # TODO: identify and count correct values (of all columns)

  # TODO: identify bad values that truly require manual inspection
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

  # TODO: identify values with incorrect formatting (and ideally correct them)
  # social security: if the value is not XXX-XX-XXXX (with dashes), add the dashes to the 9 ints

  # state: if it's not the two letter state code, assume it's the full state name and rename it to the 2 letter code

  # zip: if it's any other data type not an int, change it to an int

  # phone: should be (XXX) XXX-XXXX, so if it's not then convert the 10 numbers to that.
  # if there's a +1 at the beginning, get rid of it.

  # email: if the value is not $string@$string.$domain then it's a bad value

  # TODO: Finally, produce the 'cleaned' dataset back



  # TODO: Make a list of all the assumptions that we're making here


if __name__ == '__main__':
  main()