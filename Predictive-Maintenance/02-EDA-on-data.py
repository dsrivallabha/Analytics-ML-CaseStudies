#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 13:01:24 2019

@author: srivallabha
"""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('FanSensorData.csv', index_col=0)
print (df.describe())

#examine correlations
df.drop(columns = 'Data', inplace=True)
print (df.corr())

#plot variables and check
df.plot('Current', 'Power',kind='scatter')
df.plot('Current', 'Vibration',kind='scatter')
df.plot('Current', 'Temperature',kind='scatter')

plt.plot(df['Current'])
plt.xlabel('#Obs')
plt.ylabel('Current (A)')

plt.plot(df['Vibration'])
plt.xlabel('#Obs')
plt.ylabel('Vibration (Hz)')
