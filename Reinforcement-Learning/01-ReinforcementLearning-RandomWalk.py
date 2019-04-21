#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 18:33:28 2019

@author: srivallabha
"""

import numpy as np
#import matplotlib
import matplotlib.pyplot as plt
import os

######################################################################
######### Functions used
######################################################################

#generate maze
def generatemaze():
    n = 4
    arr = np.zeros((n,n))
    arr[1,1] = '-1'
    arr[3,1] = '-1'
#    arr[0,0] = '1'
#    arr[n,n] = ''
    return (arr)

#define the transition probability
def transprobfun(n):
    transprob = {}
    for i in range(n):
        for j in range(n):
            key = (i,j)
            val = {'N':0.25, 'E':0.25, 'S': 0.25, 'W':0.25}
            if (i==0):
                val['N'] = 0
            if (i==n-1):
                val['S'] = 0
            if (j==0):
                val['W'] = 0
            if (j==n-1):
                val['E'] = 0
            
            diff = 1 - sum(val.values())
            nonempty = 4 - diff/0.25
            #print (nonempty)
            for k in val.keys():
                if (val[k] > 0):
                    val[k] = 1./nonempty                
            transprob[key] = val
    return (transprob)

#make the next move
def step(celltup, transprob):
    mvp = transprob[celltup]
    a = [mvp[x] for x in mvp]
    mmd = np.random.choice(list(mvp), 1, p=a)
    return (mmd)

def newcoords(celltup, step):
    row,col = celltup
    if (step == 'N'):
        row -= 1
    elif (step =='E'):
        col += 1
    elif (step == 'S'):
        row += 1
    elif (step == 'W'):
        col -= 1
    return ((row,col))

def move(celltup, transprob):
    stp = step(celltup, transprob)
    #print (stp)
    newcell = newcoords(celltup, stp)
    return (newcell, stp)

def print_board(agent_position, tp, fname, count, move):
    fields = list(tp)
    board = "-----------------\n"
    for i in range(0, 16, 4):
        line = fields[i:i+4]
        for field in line:
            if field == agent_position:
                board += "| A "
            elif field == fields[0]:
                board += "| S "
            elif field == fields[-1]:
                board += "| E "
            else:
                board += "|   "
        board += "|\n"
        board += "-----------------\n"     
    #print(board)
    #plt.rc('figure', figsize=(12, 7))
    stepstr = 'step:' + str(count)
    movestr = 'move:' + str(move)
    #plt.clf()
    plt.close('all')
    plt.rc('figure', figsize=(3,3))
    plt.text(0.15, 0.8, str(stepstr), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.text(0.45, 0.8, str(movestr), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.text(0.1, 0.1, str(board), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(fname)
    return ()
    
def runonegame(tp, boardprint=0):
    maxcount = 100
    count = 0
    start = (0,0)
    end = (3,3)
    destreached = 0
    #initialize the game
    
    currcell = start
    if boardprint:
        cmd = "rm board-state-*.png"
        print ("executing command", cmd)
        os.system(cmd)
        fname = 'board-state-' + str(count).zfill(3) + '.png'
        print_board(currcell, tp, fname, count, move=' ')
        
    for i in range(maxcount):
                
        #make a move and find new cell
        newcell,stp = move(currcell, tp)
        count += 1
        
        if boardprint:    
            fname = 'board-state-' + str(count).zfill(3) + '.png'
            print_board(newcell, tp, fname, count, stp[0])
            
        if (newcell == end):
            print ('no of steps to reach the dest:', count)
            destreached = 1
            break
        else:
            currcell = newcell
    
    if (destreached == 0):
        print ('agent failed to reach destination')
        print ('steps so far', count)
    
    count2 = count + 1
    for i in range(5):        
        if boardprint:    
                fname = 'board-state-' + str(count2).zfill(3) + '.png'
                print_board(newcell, tp, fname, count, move=' ')
                count2 += 1                
    
#    if boardprint:
#        cmd = "ffmpeg -framerate 1 -i board-state-%03d.png -r 1 out.mp4"
#        print ('executing command:', cmd)
#        os.system(cmd)
#                
    return(count)
    
######################################################################
##starting the main program
maze = generatemaze()
tp = transprobfun(4)
print (tp)

runonegame(tp, 1)

#ll = []
#for i in range(1000):
#    nst = runonegame(tp)
#    if (nst < 100):
#        ll.append(nst)
#    
#print ('average number of steps for 1000 games is', np.mean(ll))
        