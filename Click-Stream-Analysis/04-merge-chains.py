# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
from utilities import *

def appendflag(df, flag):
    '''
    function to append flag to purchase chain
    '''
    for i in range(len(df)):
        aa = eval(df.channel[i])
        aa.append(flag)
        df.channel[i] = aa
        
    return (df)

#successful purchases    
df1 = pd.read_csv('Markov.csv', header=None)
df1.columns = ['channel', 'count']
df1 = appendflag(df1, 'buy')
print (df1.head())

#unsuccessful purchases
df2 = pd.read_csv('NonPurchaseMarkov.csv', header=None)
df2.columns = ['channel', 'count']
df2 = appendflag(df2, 'null')
print (df2.head())

df = df1.append(df2)
df.to_csv('FinalMarkov.csv')