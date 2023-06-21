    
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 07 13:22:11 2018
@author: jeff
"""

import pandas as pd
import sys

name = sys.argv[1]
name = name[0:-4]

read_table = pd.read_csv(name + '.csv')
l = 0
a = 0

with open(name + '.exp.fasta', 'w') as exp_out, open(name + '.uni.fasta', 'w') as uni_out:
    for index, row in read_table.iterrows():
        a = a + row.abundance
        l = l + 1
        
        print('>' + str(index) + '_unique', file=uni_out)
        print(row.sequence, file=uni_out)
        
        for i in range(1, row.abundance):
            print('>' + str(index) + '_' + str(i), file=exp_out)
            print(row.sequence, file=exp_out)
            
print (name, l, a)