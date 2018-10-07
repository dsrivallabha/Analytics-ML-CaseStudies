# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 10:34:27 2018

@author: dsrivallabha
"""
import pandas as pd
from utilities import *
###############################################################################
df = pd.read_csv('clickstream.csv', index_col=0)

purtrack = []
campdict = {}

for i in range(len(df)):
    sid = df.session[i]
    time = df.date_time[i]
    chnl = df.channel[i]
    buy = df.buy[i]
    pid = df.product_id[i]
    camp = df.campaign[i]
    
    if (chnl != '[]'):
        if sid in campdict.keys():
            campdict[sid].append([chnl, time])
        else:
            campdict[sid] = [[chnl, time]]
            
    if(buy == 1):
        try:
            purtrack.append([campdict[sid], pid, camp])
            del campdict[sid]
        except:
            purtrack.append([[chnl, time], pid, camp])
        
purdf = pd.DataFrame(purtrack)
purdf.columns = ['chain', 'pid', 'campaign']
purdf.to_csv('Purchase_Track.csv')

writedict(campdict, 'CampaignChain.csv')