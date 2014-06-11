#!/usr/bin/env python
##Nop Map Address Lookup
##SNEISIUS

from __future__ import print_function
import sys, argparse, re, operator

from elftools.common.py3compat import bytes2str
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

divLabel = "LABEL:"

normFile=''
divFile=''
outFile=''

Addresses=dict()
minAdd=None
maxAdd=None
add=0

Seen=dict()
divPos=0

def processFiles():
    #global normFile
    #global divFile
    global Addresses
    global minAdd
    global maxAdd
    global add
    global prev

    if maxAdd == None:
        print("Empty File: " + str(normFile) ) 
        return
    add=maxAdd
    prev=None
    rem=None
    while add >= minAdd:#minAdd+100: #maxAdd :
        if add in Addresses:
            #print( "\nSTART: %x"%add +":"+ str(Addresses[add]) )
            #if prev != None:
            #    print( "\nSTART: %x"%add +" -> "+ str(Addresses[add]) + ":%x"%prev )
            getDivAddress(Addresses[add])
            if rem != None:
                del Addresses[rem]
                rem=None
            rem=prev#TODO Verify... Remove prev after use but before swap
            prev=add
        add-=1


def getDivAddress(names):
    global divFile
    global Seen
    global divPos
    #TODO IF there are 2 names, THEN measure distance between them, use that for size....
    outNodes=[]

    for name in names:
        if(name in Seen):
            doAdd=True
            for outNode in outNodes:
                if Seen[name] == outNode[0]:
                    names.remove(name)
                    doAdd=False
                    del Seen[name]
                    break # Remove dupes
            if doAdd:
                node = [Seen[name], name]
                outNodes.append(node)
                names.remove(name)
                del Seen[name]
            
    if (len(names)!=0):
        elffile = ELFFile(divFile)
        section = elffile.get_section_by_name(b'.symtab')
        if not section:
            print('ERROR: No symbol table found. Perhaps this ELF has been stripped?')
            sys.exit(0)
        if isinstance(section, SymbolTableSection):
            num_symbols = section.num_symbols()
            while(divPos < num_symbols):
                if (section.get_symbol(divPos).entry['st_value'] == 0):
                    divPos+=1
                    continue # No 0 address labels
                if (section.get_symbol(divPos).name.find(divLabel) == -1):
                    divPos+=1
                    continue # Only valid Labels
                if (section.get_symbol(divPos).name in names):
                    doAdd=True
                    for outNode in outNodes:
                        if section.get_symbol(divPos).entry['st_value'] == outNode[0]:
                            names.remove(section.get_symbol(divPos).name)
                            doAdd=False
                            break # Remove dupes
                    if doAdd:
                        node = [section.get_symbol(divPos).entry['st_value'], section.get_symbol(divPos).name]
                        outNodes.append(node)
                        names.remove(section.get_symbol(divPos).name)
                    if (len(names)==0):
                        divPos+=1
                        break
                else:
                    Seen[section.get_symbol(divPos).name]=section.get_symbol(divPos).entry['st_value']
                divPos+=1

    #size=getInstrLen()
    size=1
    if prev != None and prev-add > 0:
        size=prev-add
    if len(outNodes) == 0:
        #print("No Matching Label Found: "+str(names))
        return
    elif len(outNodes) == 1:
        divAdd, label = outNodes[0]
        printMapping(divAdd, size, add, size, label)
    elif len(outNodes) == 2:
#TODO if calculated size = div size then either the opposite size is the same or we found known size, either way the other one is unknown
#reverse order scanning may prevent this need
        if outNodes[0][0] > outNodes[1][0]:
            divSize = outNodes[0][0] - outNodes[1][0]
            divAdd, label = outNodes[1]
            printMapping(divAdd, divSize, add, size, label)
            divAdd, label = outNodes[0]
            printMapping(divAdd, size, add, size, label)
        else:
            divSize = outNodes[1][0] - outNodes[0][0]
            divAdd, label = outNodes[0]
            printMapping(divAdd, divSize, add, size, label)
            divAdd, label = outNodes[1]
            printMapping(divAdd, size, add, size, label)
    else:
        print("ERROR: More than 2 not planned for\n"+str(outNodes))
        for outNode in outNodes:
            divAdd, label = outNode
            printMapping(divAdd, size, add, size, label)
            

    return

def printMapping(divAdd, divSize, normAdd, normSize, label):
    #print("FOUND: "+ label +" -> %x"%divAdd + ":"+str(divSize) +"  -> %x"%normAdd+":"+str(normSize) )
    output_address_map(divAdd, divSize, normAdd, normSize, label)

def getInstrLen():
    if add == maxAdd:
        return 1
    i=add+1
    while i < maxAdd and i not in Addresses:
        i+=1
    if i-add==0:
        return 1
    return i-add



def getAddresses():
    global normFile
    global Addresses
    global minAdd
    global maxAdd

    elffile = ELFFile(normFile)
    section = elffile.get_section_by_name(b'.symtab')

    if not section:
        print('ERROR: No symbol table found. Perhaps this ELF has been stripped?')
        sys.exit(0)

    if isinstance(section, SymbolTableSection):
        num_symbols = section.num_symbols()
        for i in range(0,num_symbols):
            if (section.get_symbol(i).entry['st_value'] == 0):
                continue # No 0 address labels
            if (section.get_symbol(i).name.find(divLabel) == -1):
                continue # Only valid Labels

            key = section.get_symbol(i).entry['st_value']

            if minAdd == None or maxAdd == None:
                minAdd = key
                maxAdd = key
            elif key < minAdd:
                minAdd = key
            elif key > maxAdd:
                maxAdd = key

            #print(str(Addresses) + " <- " + key)
            if key not in Addresses:
                #print("Added: " + section.get_symbol(i).name)
                Addresses[key] = [section.get_symbol(i).name]
            else:
                Addresses[key].append(section.get_symbol(i).name)
                #print("Dupe: " + section.get_symbol(i).name + " -> " + str(key) + " !!! " + str(Addresses[key]) )
    #print("MIN: " + str(minAdd) +"\tMAX: "+str(maxAdd) )

def output_address_map(divAdd, divSize, normAdd, normSize, labelID):
    labelID = labelID.strip()
    try:
        outFile.write("%x" % divAdd)
        outFile.write(':')
        outFile.write("%x" % divSize)
        outFile.write('::')
        outFile.write("%x" % normAdd)
        outFile.write(':')
        outFile.write("%x" % normSize)
        outFile.write("\t#%s" % labelID)
        outFile.write('\n')
    except KeyError as e:
        print ("Could NOT find: %s" % e)
    outFile.flush()


def parse_args():
    global divFile
    global normFile
    global outFile

    parser = argparse.ArgumentParser(description='Nop Map Address Lookup')

    parser.add_argument('-d', '--divFile', type=argparse.FileType('rb'), help='Diversified File', required=True, dest='divFile')
    parser.add_argument('-n', '--normFile', type=argparse.FileType('rb'), help='Normailized File (divFile.norm)', dest='normFile')
    parser.add_argument('-o', '--outFile', type=argparse.FileType('w'), help='Output File (divFile.nmap)', dest='outFile')

    args = parser.parse_args()

    globals().update(vars(args))

    if not ( isinstance(normFile, file) ):
        normFilename = '%s.norm' % divFile.name
        normFile = open(normFilename, 'rb')
        print ("AUTO normFile = %s" % normFilename )

    if not ( isinstance(outFile, file) ):
        outFilename = '%s.divmap' % divFile.name
        outFile = open(outFilename, 'w')
        print ("AUTO outFile = %s" % outFilename )

if __name__ == '__main__':
    print ("=-" * 40)

    parse_args()
    print ("=-" * 40)

    print ("divFile: %s" % divFile.name )
    print ("normFile: %s" % normFile.name )
    print ("outFile: %s" % outFile.name )
    print ("=-" * 40)

    getAddresses()

    processFiles()

    divFile.close()
    normFile.close()
    outFile.close()



