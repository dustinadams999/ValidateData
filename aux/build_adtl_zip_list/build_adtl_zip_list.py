# this program builds a dictionary of all valid zip codes for each state
# with the key being the full state name. 
# the raw data comes from https://www.zipcodestogo.com/

import json
import sys
import os
from IPython import embed as shell

all_states = {}

for filename in os.listdir('/Users/dustinadams/quicken_code_test/ValidateData/aux/build_adtl_zip_list'):
  if filename[-3:] != 'txt':
    continue

  state = ''
  if len(filename.split('_')) == 2:
    state = filename.split('_')[0].capitalize()
  else:
    state = filename.split('_')[0].capitalize() + ' ' + filename.split('_')[1].capitalize()
    

  f = open(filename, 'r')

  lines = [a.replace('\n', '') for a in f.readlines()]

  zips = []

  for line in lines:
      for a in line.split():
          if len(a) == 5 and a.isnumeric():
              zips.append(a)

  all_states[state] = zips

with open('additional_state_data.json', 'w') as state_file:
    json.dump(all_states, state_file)
