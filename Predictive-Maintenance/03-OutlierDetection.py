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

classifier = EllipticEnvelope(contamination=0.02)
df = pd.read_csv('FanSensorData.csv')

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

# Get the boundary for various combinations
X1 = df[['Current', 'Power']]
clf, b = getoutlier(X1, classifier)

X1 = df[['Current', 'Vibration']]
clf, b = getoutlier(X1, classifier)

X1 = df[['Vibration', 'Temperature']]
b = getoutlier(X1, classifier)