# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
from utilities import *
###############################################################################    
def markchain(mk):
    '''
    function to generate markov chain
    '''
    mk = eval(mk)
    
    cc = []
    if any(isinstance(el, list) for el in mk):
        for i in range(len(mk)):
            jj = mk[i]
            print (jj)
            if (jj[0] != '[]'):
                cc.append(jj[0])
    cct = str(cc)
    return (cct)
###############################################################################
    
df = pd.read_csv('Purchase_Track.csv')
print (df.head())

markovdict = {}
for i in range(len(df)):
    print(df.chain[i])
    mkc = markchain(df.chain[i])
    if (mkc in markovdict.keys()):
        markovdict[mkc] += 1
    else:
        markovdict[mkc] = 1

writedict(markovdict, 'Markov.csv')


df2 = pd.read_csv('CampaignChain.csv', header=None)
df2.columns = ['session', 'chain']
print (df2.head())

umarkovdict = {}
for i in range(len(df2)):
    print(df2.chain[i])
    mkc = markchain(df2.chain[i])
    if (mkc in umarkovdict.keys()):
        umarkovdict[mkc] += 1
    else:
        umarkovdict[mkc] = 1

writedict(umarkovdict, 'NonPurchaseMarkov.csv')

