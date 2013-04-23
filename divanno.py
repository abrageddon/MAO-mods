#!/usr/bin/python
import sys
import re
import random

##parser = argparse.ArgumentParser(description='Diversify Annotated Assembly.')
##parser.add_argument('integers', metavar='N', type=int, nargs='+',
##                   help='an integer for the accumulator')


#Get file
if(len(sys.argv)<=1):
    inFile="SmallTestProgram/hellofunc.a.s"
else:
    inFile=sys.argv[1]

#TODO: check for proper extension (.a.s) annotated source
    
print inFile

#Open output file
outFile=inFile[:-3] + 'div.s'

print outFile

inf = open(inFile,'r')
outf = open(outFile,'w')

#For each line in input
for line in inf:
    #If MC exists for this line; then diversify
    if ('# MC=' in line):
        print('\n'+line.rstrip())
        mcArgs=re.sub(r'.*# MC=(?P<OUT>[^ ]*).*',r'\g<OUT>',line.rstrip())
        print('mcArgs: ' + mcArgs)
        
        #TODO: PROFILE DATA!!!
        
        #If can insert NOP and we roll success; then insert it before line
        if ('N' in mcArgs and random.randint(0,100) <= 30):
            #TODO: other NOPS
            print ('NOP')
            outf.write('\tnop\n')
            
        #If can MOV To LEA and we roll success; then modify line
        if ('M' in mcArgs and random.randint(0,100) <= 30):
            #TODO: re.sub for MOVToLEA
            outf.write(line)
            print ('MOVToLEA')
        else:#Else just copy
            outf.write(line)
    else:#Else just copy
        outf.write(line)
    
    
inf.close()
outf.close()