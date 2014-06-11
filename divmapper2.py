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
normAddresses=dict()
normSizes=dict()
divAddresses=dict()
divSizes=dict()

outAddresses=dict()
outSizes=dict()

def process_file(stream, isNorm):
    global normAddresses
    global normSizes
    global divAddresses
    global divSizes

    elffile = ELFFile(stream)
    section = elffile.get_section_by_name(b'.symtab')

    if not section:
        print('ERROR: No symbol table found. Perhaps this ELF has been stripped?')
        sys.exit(0)

    # bytes2str is used to print the name of the section for consistency of
    # output between Python 2 and 3. The section name is a bytes object.

    if isinstance(section, SymbolTableSection):
        num_symbols = section.num_symbols()
        for i in range(0,num_symbols):
#TODO UNIQUE ADDRESSES...
            if (section.get_symbol(i).entry['st_value'] == 0):
                continue
            if (section.get_symbol(i).name.find(divLabel) == -1):
                continue #Only valid Labels
            #print('%s : %x' % (section.get_symbol(i).name, section.get_symbol(i).entry['st_value']) )
            if (isNorm):
                normAddresses[section.get_symbol(i).name] = section.get_symbol(i).entry['st_value']
            else:
                divAddresses[section.get_symbol(i).name] = section.get_symbol(i).entry['st_value']

def calculate_sizes(sorted_list):
    startAdd=0
    startKey=0
    sizes={}
    #TODO calculate size without nops; combine contiguous
#TODO PROCESS IN VALUE (address) ORDER
    #for key, value in sorted_list:
    for key in sorted_list:
        value = sorted_list[key]
        #print(str(key) + ":" + str(value))
        sizes[key] = 1
        if startAdd != 0:
            sizes[startKey] = value - startAdd
            if sizes[startKey] == 0:
                sizes[startKey] = 1
            #	print(startKey + " !=! " +str(sizes[startKey]))
        startAdd = value
        startKey = key
    return sizes

def output_file():
#TODO NO MORE SORTING?
    #sorted_normAddresses = sorted(normAddresses.iteritems(), key=operator.itemgetter(1))
    #sorted_divAddresses = sorted(divAddresses.iteritems(), key=operator.itemgetter(1))

    #process sizes
    global normSizes
    global divSizes
    #normSizes = calculate_sizes(sorted_normAddresses);
    #divSizes = calculate_sizes(sorted_divAddresses);
    normSizes = calculate_sizes(normAddresses);
    divSizes = calculate_sizes(divAddresses);

    #TODO COMBINE CONTIGUOUS SECTIONS

    #print (str(normAddresses))

    #for key, value in sorted_normAddresses:
    for key in normAddresses:
        #print( str(key) + ":" + str(value) )
        output_address_map(key)

def output_address_map(labelID):
    labelID = labelID.strip()
    try:
        outFile.write("%x" % divAddresses[labelID])
        outFile.write(':')
        outFile.write("%x" % divSizes[labelID])
        outFile.write('::')
    #except KeyError as e:
        #print ("Could NOT find div: %s" % e)
    #try:
        outFile.write("%x" % normAddresses[labelID])
        outFile.write(':')
        outFile.write("%x" % normSizes[labelID])
        outFile.write("\t#%s" % labelID)
        outFile.write('\n')
    except KeyError as e:
        print ("Could NOT find: %s" % e)


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

    process_file(divFile, False)
    divFile.close()
    process_file(normFile, True)
    normFile.close()

    output_file()
    outFile.close()



