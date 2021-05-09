# this file builds a dictionary encoded in json of states names and their
# corresponding two letter state code.
# usage: $ python rewrite.py states.txt

import json

f = open('states.txt','r')
states = [a.replace('\n','') for a in f.readlines()]

states_dict = {}

for state in states:
    key = ''
    for k in state.split()[:-1]:
        key = (key + k + ' ')
    key = key.strip()
    value = state.split()[-1:][0]
    states_dict[key] = value

with open('states.json', 'w') as state_file:
    json.dump(states_dict, state_file)
