#!/usr/bin/python
import sys
import re
import random

def main():
    ##TODO: Get file better
    #Get file
    if(len(sys.argv)<=1):
        inFile="SmallTestProgram/hellofunc.a.s"
    else:
        inFile=sys.argv[1]

    ##TODO: check for proper extension (.a.s) annotated source
        
    print inFile

    #Open output file
    outFile=inFile[:-3] + 'div.s'

    print outFile

    inf = open(inFile,'r')
    outf = open(outFile,'w')

    reArgs = re.compile(r'.*# MC=(?P<OUT>[^ ]*).*')
    ##TODO: change SUF to arch compatable version
    reMov2Lea = re.compile(r'mov(?P<SUF>[lq]+)\s+(?P<ONE>.+),\s*(?P<TWO>.+)')

    #For each line in input
    for line in inf:
        #If MC exists for this line; then diversify
        if ('# MC=' in line):
            mcArgs=re.sub(reArgs,r'\g<OUT>',line)
            
            #TODO: PROFILE DATA!!!
            
            #If can insert NOP and we roll success; then insert NOP before current line
            if ('N' in mcArgs):
                if (roll()):
                    outf.write( nop64(random.randint(0,4)) )#64bit
            elif ('n' in mcArgs ):
                if (roll()):
                    outf.write( nop32(random.randint(0,4)) )#32bit
                
            #If can MOV To LEA and we roll success; then modify line
            if ('M' in mcArgs and roll()):
                ##TODO: change SUF to arch compatable version
                outf.write(re.sub(reMov2Lea,
                                   'lea\g<SUF>\t(\g<ONE>), \g<TWO>'
                                   ,line))
            else:#Else print line unchanged
                outf.write(line)
        else:#Else no annotations, just write
            outf.write(line)
        
        
    inf.close()
    outf.close()


def nop64(x):
    return {
        0:'\tnop\n',
        1:'\tmovq\t%rbp, %rbp\n',
        2:'\tmovq\t%rsp, %rsp\n',
        3:'\tleaq\t(%rdi), %rdi\n',
        4:'\tleaq\t(%rsi), %rsi\n',
    }[x]
    
def nop32(x):
    return {
        0:'\tnop\n',
        1:'\tmovl\t%ebp, %ebp\n',
        2:'\tmovl\t%esp, %esp\n',
        3:'\tleal\t(%edi), %edi\n',
        4:'\tleal\t(%esi), %esi\n',
    }[x]

def roll():
    return (random.randint(0,100) <= 30)


if __name__ == "__main__":
    main()
    
    
    
    
    
