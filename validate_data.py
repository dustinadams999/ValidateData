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

num_empty_soc_secs = df.isnull().sum()[0]
num_empty_states = df.isnull().sum()[1]
num_empty_zips = df.isnull().sum()[2]
num_empty_phones = df.isnull().sum()[3]
num_empty_emails = df.isnull().sum()[4]

shell()