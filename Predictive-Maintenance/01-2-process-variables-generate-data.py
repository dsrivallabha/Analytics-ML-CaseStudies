#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 07:20:03 2019

@author: srivallabha
"""

import pandas as pd
import numpy as np

df = pd.read_csv('test.csv')

#make values non zeros
minn = df.min().min()
print (minn)
df = df - minn
print (df.corr())

df.describe()
print (df.columns)

#get the mean values
cmean = 0.75 #Amperes
pmean = 90 #Watts
vmean = 8 #Hertz
Tmean = 14 #Centigrade

df1 = df.copy()

#scale data to get the actual numbers
df1['Current'] = df1['Current'] * cmean
df1['Power'] = df1['Power'] * pmean
df1['Vibration'] = df1['Vibration'] * vmean
df1['Temperature'] = df1['Temperature'] * Tmean
df1['Data'] = 0
#check if correlations have changed
print (df1.corr())
print (df1.describe())

#create outliers
datalen = len(df1)

#2% outliers in the first half of the data set
n1 = int(0.5 * datalen)
n1samples = int(0.02 * n1)
set1 = np.random.randint(0, n1, n1samples)

#5% outliers from 50 to 80% of data
n2 = int(0.8 * datalen)
n2samples = int(0.05 * (n2-n1))
set2 = np.random.randint(n1, n2, n2samples)

#10% outliers from 80% to end of data
n3samples = int(0.10 * (datalen - n2))
set3 = np.random.randint(n2, datalen, n3samples)
print (n1samples, n2samples, n3samples)

setf = list(set1) + list(set2) + list(set3)

counter = 0
for i in setf:
    print (i)
    #change either vibration or current
    if (np.mod(counter,2) == 0):
        df1['Current'].iloc[i] = np.random.uniform(0, 1) * df1['Current'].iloc[i]
    else:
        df['Vibration'].iloc[i] = np.random.uniform(0,1) * df1['Vibration'].iloc[i]
    df1['Data'].iloc[i] = 1
    counter += 1
df1.to_csv('FanSensorData.csv')