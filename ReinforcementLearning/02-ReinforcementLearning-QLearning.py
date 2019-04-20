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
def qlearn():
    arr = np.zeros((5,4))
    return (arr)

def decode(step):
    mve = {0:'N', 1:'E', 2:'S', 3:'W'}
    return (mve[step])

def qtabledict(celltup, mv):
    pos = 'interior'
    if (celltup[0] == 0):
        pos = 'left'
    elif (celltup[0] == 3):
        pos = 'right'
    if (celltup[1] == 0):
        pos = 'top'
    elif (celltup[1] == 3):
        pos = 'bottom'
        
    qtd = {'left': 0, 'right': 1, 'top':2, 'bottom':3, 'interior':4}
    mve = {'N':0, 'E':1, 'S':2, 'W':3}
    return (qtd[pos], mve[mv])

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

def getreward(cell):
    nr, nc = cell
    rewards = 0
    if (cell[0] < 0):
        rewards = -1
        nr = 0
    if (cell[1] < 0):
        rewards = -1
        nc = 0
    if (cell[0] > 3):
        rewards = -1
        nr = 3
    if (cell[1] > 3):
        rewards = -1
        nc = 3
    if (cell == (3,3)):
        rewards = 10
    newcell = (nr,nc)
    return (newcell, rewards)


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

def print_board(agent_position, tp, fname, count, move,reward):
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
    rewardstr = 'reward:' + str(reward)
    #plt.clf()
    plt.close('all')
    plt.rc('figure', figsize=(3,3))
    plt.text(0.15, 0.9, str(stepstr), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.text(0.45, 0.9, str(movestr), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.text(0.25, 0.8, str(rewardstr), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.text(0.1, 0.1, str(board), {'fontsize': 10}, fontproperties = 'monospace') # approach improved by OP -> monospace!
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(fname)
    return ()

    
######################################################################
Q = qlearn()   
start = (0,0)
alpha = 0.5
gamma = 0.1

tp = transprobfun(4)

print_board((0,0), tp, 'tst.png', 1, 'E', 1)

currcell = start
count = 0
fname = 'board-state-' + str(count).zfill(3) + '.png'
print_board(currcell, tp, fname, count, ' ', 0)


for i in range(100):
    
    print ('currcell: ', currcell)
    
    #make a mew
    mve = np.random.choice(['N', 'E', 'S', 'W'])
    print (mve)
    
    #get the cell position in qtabledict for the current cell and move
    (currrow, currcol) = qtabledict(currcell, mve)
    print (currrow, currcol)
    
    #move to new cell
    newcell = newcoords(currcell, mve)

    #get the reward for newcell and newcell coordinates  
    newcell, reward = getreward(newcell)
    
    print ('newcell, reward:', newcell, reward)
    
    
    
    (newrow, newcol) = qtabledict(newcell, mve)
    nextmaxre  = np.argmax(Q[newrow,:])
    print ('nextmaxreward', nextmaxre)

    Q[currrow, currcol] += alpha * (reward + gamma * nextmaxre - Q[currrow, currcol])
    
    currcell = newcell
    
    count += 1
    
    fname = 'board-state-' + str(count).zfill(3) + '.png'
    print_board(currcell, tp, fname, count, mve, reward)
    

print (Q)

currcell = start
count = 0
fname = 'board-state-' + str(count).zfill(3) + '.png'
print_board(currcell, tp, fname, count, ' ', reward=0)

for k in range(100):
    print ('current cell:', currcell)
    mve = np.random.choice(['N', 'E', 'S', 'W'])
    (cr,cc) = qtabledict(currcell, mve)
    print (cr,cc)
    print (np.argmax(Q[cr,:]))
    mv = decode(np.argmax(Q[cr,:]))
    print (mv)
    currcell = newcoords(currcell, mv)
    
    if (currcell == (3,3)):
        reward = 10
    else:
        reward = 0
    
    count += 1
    fname = 'board-state-' + str(count).zfill(3) + '.png'
    print_board(currcell, tp, fname, count, mv, reward)
        
    if (currcell == (3,3)):
        print ('reached destination in', count)
        break
        
        
    