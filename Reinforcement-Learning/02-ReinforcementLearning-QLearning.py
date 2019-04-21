#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 18:33:28 2019


@author: srivallabha
"""

import numpy as np
import matplotlib.pyplot as plt

######################################################################
######### Functions used
######################################################################
def qlearn(n):
    arr = np.zeros((n+1,n))
    return (arr)

def decode(step):
    mve = {0:'N', 1:'E', 2:'S', 3:'W'}
    return (mve[step])

def qtabledict(celltup, mv, n):
    pos = 'interior'
    if (celltup[0] == 0):
        pos = 'left'
    elif (celltup[0] == n-1):
        pos = 'right'
    if (celltup[1] == 0):
        pos = 'top'
    elif (celltup[1] == n-1):
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

def getreward(cell, n):
    nr, nc = cell
    rewards = 0
    if (cell[0] < 0):
        rewards = -1
        nr = 0
    if (cell[1] < 0):
        rewards = -1
        nc = 0
    if (cell[0] > n-1):
        rewards = -1
        nr = 3
    if (cell[1] > n-1):
        rewards = -1
        nc = 3
    if (cell == (n-1,n-1)):
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
            #four movement direction, so nonempty is 4 - diff/0.24
            nonempty = 4 - diff/0.25
            #print (nonempty)
            for k in val.keys():
                if (val[k] > 0):
                    val[k] = 1./nonempty                
            transprob[key] = val
    return (transprob)

def print_board(agent_position, tp, fname, count, move,reward, n):
    fields = list(tp)
    board = "-----------------\n"     
    for i in range(0, n*n, n):
        line = fields[i:i+n]
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
## Main program
    
#set the size of the maze
n = 4

# define the q learning matrix
Q = qlearn(n)
print (Q)

#set the parameters for learning   
alpha = 0.5
gamma = 0.1

#set the starting point (this will always be (0,0))
start = (0,0)

#get the transition probability matrix for random walk
tp = transprobfun(n)
print (tp)

#print test board
#print_board((0,0), tp, 'tst.png', 1, 'E', 1)

#print the first board
currcell = start
count = 0
fname = 'board-state-' + str(count).zfill(3) + '.png'
print_board(currcell, tp, fname, count, ' ', 0, n)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#Step 1. Exploration phase
for i in range(100):
    
    #print current cell state
    #print ('currcell: ', currcell)
    
    #make a move
    mve = np.random.choice(['N', 'E', 'S', 'W'])
    #print (mve)
    
    #get the cell position in qtabledict for the current cell and move
    (currrow, currcol) = qtabledict(currcell, mve, n)
    #print (currrow, currcol)
    
    #move to new cell
    newcell = newcoords(currcell, mve)

    #get the reward for newcell and newcell coordinates  
    newcell, reward = getreward(newcell, n)
    #print ('newcell, reward:', newcell, reward)
        
    #get the new row and column from the qtable dict for the new cell 
    #and previous move - previous move is not used, only a place holder
    (newrow, newcol) = qtabledict(newcell, mve, n)
    
    #get the maximum reward in the new state
    nextmaxre  = np.argmax(Q[newrow,:])
    #print ('nextmaxreward', nextmaxre)


    #update the Q matrix
    Q[currrow, currcol] += alpha * (reward + gamma * nextmaxre - Q[currrow, currcol])
    
    #set the new cell to the current cell
    currcell = newcell
    
    #update count
    count += 1
    
    #print the board
    fname = 'board-state-' + str(count).zfill(3) + '.png'
    print_board(currcell, tp, fname, count, mve, reward, n)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#print the Q table
print (Q)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#Step 2. Exploitation phase
currcell = start
count = 0

#print the board
fname = 'board-state-' + str(count).zfill(3) + '.png'
print_board(currcell, tp, fname, count, ' ', 0, n)

print (n)
#set max steps and try to move
for k in range(100):
    #print ('current cell:', currcell)
    
    
    #make a random move to get position in qtable
    mve = np.random.choice(['N', 'E', 'S', 'W'])
    (cr,cc) = qtabledict(currcell, mve, n)    
    #print (cr,cc)
    #print (np.argmax(Q[cr,:]))
    
    #move in the direction of maximum reward
    mv = decode(np.argmax(Q[cr,:]))
    print (mv)
    
    #get the new cell based on move direction
    currcell = newcoords(currcell, mv)
    
    # get reward to show in the board
    if (currcell == (n-1, n-1)):
        reward = 10
    else:
        reward = 0
    
    #update count and print board
    count += 1
    fname = 'board-state-' + str(count).zfill(3) + '.png'
    print_board(currcell, tp, fname, count, mv, reward, n)
        
    if (currcell == (n-1,n-1)):
        print ('reached destination in', count)
        break