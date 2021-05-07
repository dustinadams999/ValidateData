import sys
import numpy as np
import pandas as pd
from IPython import embed as shell

df = pd.read_csv('data_quality_case_study.csv')

soc_secs = np.array(df['social_security'])
states = np.array(df['state'])
zips = np.array(df['zip'])
phones = np.array(df['phone1'])
emails = np.array(df['email'])

num_empty_soc_secs = len([a for a in list(df['social_security'].isnull()) if a])
num_empty_states = len([a for a in list(df['state'].isnull()) if a])
num_empty_zips = len([a for a in list(df['zip'].isnull()) if a])
num_empty_phones = len([a for a in list(df['phone1'].isnull()) if a])
num_empty_emails = len([a for a in list(df['email'].isnull()) if a])

shell()