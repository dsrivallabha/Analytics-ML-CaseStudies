#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 14:26:20 2019

@author: srivallabha
"""
import pandas as pd
import numpy as np
from sklearn.covariance import EllipticEnvelope
import matplotlib.pyplot as plt

def getoutlier(df, classifier):
    names = df.columns
    print (names)
    data = np.array(df)
    xmin = min(data[:,0])
    xmax = max(data[:,0])
    ymin = min(data[:,1])
    ymax = max(data[:,1])
    xx1, yy1 = np.meshgrid(np.linspace(xmin, xmax, 500), 
                       np.linspace(ymin, ymax, 500))
    clf = classifier.fit(data)
    Z1 = clf.decision_function(np.c_[xx1.ravel(), yy1.ravel()])
    Z1 = Z1.reshape(xx1.shape)
    
    #a = plt.figure(1)  # two clusters
    a = plt.figure()
    _ = plt.contour(xx1, yy1, Z1, levels=[0], linewidths=2, colors='black')
    _ = plt.scatter(data[:, 0], data[:, 1], color='blue')
    _ = plt.xlabel(names[0])
    _ = plt.ylabel(names[1])
    return (clf, a)

#set the classifier
classifier = EllipticEnvelope(contamination=0.02)

#read the data
dfdata = pd.read_csv('FanSensorData.csv')
#data collected at frequency of 1 minute
# 1 day has 24*60 = 1440 observations
ndays = int(len(dfdata)/(24.*60))
print (ndays)

#split data into training and test
dftrain, dftest = np.split(dfdata, [int(0.5*len(dfdata))])
print (len(dftrain), len(dftest))

#train the model on training data for current and vibration
X1 = dftrain[['Current', 'Vibration']]
clf, b = getoutlier(X1, classifier)

#for the rest of the data,
counter = 0
ll = []
#for i in range(int(ndays/2), ndays):
for i in range(ndays):    
    dfdaily = dfdata[counter:counter+1440]
    X2 = np.array(dfdaily[['Current', 'Vibration']])
    Y2 = clf.predict(X2)
    outper = (sum(Y2== -1))/1440. * 100
    print (i, outper) 
    ll.append([i, outper])
    counter += 1440
    
lldf = pd.DataFrame(ll)
lldf.columns = ['Day', '% Outliers']
lldf.to_csv('Predictions.csv')

lldf.plot('Day', '% Outliers')