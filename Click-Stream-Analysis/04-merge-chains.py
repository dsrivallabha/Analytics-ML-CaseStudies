# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd

#successful purchases    
df1 = pd.read_csv('Markov.csv', header=None)
df1.columns = ['Channel', 'Count']
print (df1.head())

#unsuccessful purchases
df2 = pd.read_csv('NonPurchaseMarkov.csv', header=None)
df2.columns = ['Channel', 'NonConversionCount']
print (df2.head())

df3 = pd.merge(df1, df2, how='outer', on = ['Channel'])
#replace nas with zero
df3['Count'] = df3['Count'].fillna(0)
df3['NonConversionCount'] = df3['NonConversionCount'].fillna(0)
df3.head()
df3.to_csv('MergedChains.csv')