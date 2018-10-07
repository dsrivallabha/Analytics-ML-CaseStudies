# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import numpy as np
import datetime as dt
###############################################################################    
def gensessid(n):
    '''
    function to generate random numbers
    '''
    for i in range(n):
        z = np.random.randint(5, 25)
        yield (z)
###############################################################################    
def gentime(n):
    '''
    function to generate random time events
    '''
    for i in range(n):
        z = np.random.randint(5, 345)
        yield (z)
###############################################################################
def genchannels():
    '''
    function to generate channels
    '''
    #channel
    channels = ['goog', 'fb', 'insta', 'twit']

    c1 = np.random.random()
    if (c1< 0.4):
        c= []
    else:
        c = np.random.choice(channels)
    return (c)
###############################################################################
def picksession(sesslist, gens):
    '''
    function to pick session id
    '''
    z = np.random.random()
    if (z<0.7):
        ss = np.random.choice(sesslist)
    else:
        ss = sesslist[-1] + next(gens)
    return (ss)       
###############################################################################
def getproid(prlist):
    '''
    function to return product id
    '''    
    z = np.random.random()
    if (z<0.25):
        pid = prlist[0]
    elif (z< 0.45):
        pid = prlist[1]
    else:
        pid = np.random.choice(prlist[2:])
    return (pid)
###############################################################################    
def buy(pid, prlist):
    ''''
    function to return a campaign 
    '''
    if (pid==prlist[0]):
        f = int(np.random.random() + 0.6)
    elif (pid==prlist[1]):
        f = int(np.random.random() + 0.05)
    else:
        f = int(np.random.random() + 0.2)
    return (f)
###############################################################################    
def campaign(e):
    ''''
    function to return a campaign 
    '''
    if (e==1):
        f = int(np.random.random() + 0.6)
    else:
        f = 0
    return (f)
###############################################################################    

#MAIN PROGRAM
    
#session id
ses_start = 129894938431

#date
strt_date = dt.datetime.strptime("2017-08-01 09:00:00", "%Y-%m-%d %H:%M:%S")

#product ids
prodid = np.random.randint(1001, 1543, 60)

# observations
nobs = 10000

sessgen = gensessid(nobs)
timegen = gentime(nobs)

data = []
sesslist = []
ff = 0
for i in range(nobs):
    if (ff==0):
        a = ses_start
        b = strt_date
        c = genchannels()
        d = getproid(prodid)
        e = buy(d, prodid)
        f = campaign(e)
        sesslist.append(a)
        ff= -1
    else:
        a = picksession(sesslist, sessgen)
        b += dt.timedelta(seconds = next(timegen))
        c = genchannels()
        d = getproid(prodid)
        e = buy(d, prodid)
        f = campaign(e)
        
        if (a not in sesslist):
            sesslist.append(a)
    
    data.append([a,b,c,d, e,f])
    
ddf = pd.DataFrame(data)
ddf.columns = ['session', 'date_time', 'channel', 'product_id', 'buy', 'campaign']
ddf.to_csv('clickstream.csv')
