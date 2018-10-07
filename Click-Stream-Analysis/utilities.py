# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 10:34:27 2018

@author: dsrivallabha
"""
import csv
import pandas as pd

###############################################################################
def writedict(mydict, filename):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for key, value in mydict.items():
            writer.writerow([key, value])
    return ()
###############################################################################
def readdict(filename):
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file)
        d = {}
        for row in reader:
            k, v = row
            d[k] = v
    return (d)
###############################################################################