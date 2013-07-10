#!/usr/bin/python
import sys, re
import MySQLdb as mdb
from warnings import filterwarnings
connection = None

#
# Pass text file containing the output of -ftime-report to parse and insert values into MySQL 
# Running without parameter outputs values stored in DB
# MUST run with -j1 or the output isn't consistent
#

def globalConnect():
    # Global settings
    global connection
    # Server, User, Pass, Database
    connection = mdb.connect('localhost', 'local', 'local', 'timereport')
    connection.autocommit(True)


def main():
    try:
        globalConnect()
        if (len(sys.argv) >1 and sys.argv[1] is not None):
            # TODO just print results
            
            inTimes = open(sys.argv[1],'r')
            
            global connection
            filterwarnings('ignore', category = mdb.Warning)
            cur = connection.cursor()
            # Setup tables if needed MYSQL
            cur.execute("""CREATE TABLE IF NOT EXISTS `Register_Allocation` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `User_System` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `Pass_execution_timing_report` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `User_System` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `Miscellaneous_Ungrouped_Timers` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `User_System` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `Instruction_Selection_and_Scheduling` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `User_System` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `DWARF_Emission` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `User_System` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `gcc` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `gccTime` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cur.execute("""CREATE TABLE IF NOT EXISTS `other` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `User_Time` float DEFAULT '0',
  `System_Time` float DEFAULT '0',
  `Wall_Time` float NOT NULL,
  `Name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")
            cleanTables()
            
            while True:
                line = inTimes.readline()
                if not line:
                    sys.stdout.write('\n')
                    break # EOF
                sys.stdout.write('.')
                #print line
                
                
                # Register Allocation
                if ('Register Allocation' in line):
#                    print 'Register Allocation'
                    line = inTimes.readline() # skip divider
                    line = inTimes.readline() # skip total exec time
                    line = inTimes.readline() # skip white space
                    
                    # get categories
                    line = inTimes.readline()
                    categories = getCategories(line)
                    
                    cont = True
                    while cont:
                        line = inTimes.readline().strip()
                        times = ''
                        if lineTest(line): cont=False
                        else: 
                            times = getTimes(line)
#                            writeTimes(categories, times)
                            insertTimes('Register_Allocation',categories, times)
                        
                
                # Instruction Selection and Scheduling
                if ('Instruction Selection and Scheduling' in line):
#                    print 'Instruction Selection and Scheduling'
                    line = inTimes.readline() # skip divider
                    line = inTimes.readline() # skip total exec time
                    line = inTimes.readline() # skip white space
                    
                    # get categories
                    line = inTimes.readline()
                    categories = getCategories(line)
                    
                    cont = True
                    while cont:
                        line = inTimes.readline().strip()
                        times = ''
                        if lineTest(line): cont=False
                        else: 
                            times = getTimes(line)
#                            writeTimes(categories, times)
                            insertTimes('Instruction_Selection_and_Scheduling',categories, times)
            
            
                # DWARF Emission
                if ('DWARF Emission' in line):
#                    print 'DWARF Emission'
                    line = inTimes.readline() # skip divider
                    line = inTimes.readline() # skip total exec time
                    line = inTimes.readline() # skip white space
                    
                    # get categories
                    line = inTimes.readline()
                    categories = getCategories(line)
                    
                    cont = True
                    while cont:
                        line = inTimes.readline().strip()
                        times = ''
                        if lineTest(line): cont=False
                        else: 
                            times = getTimes(line)
#                            writeTimes(categories, times)
                            insertTimes('DWARF_Emission',categories, times)
    

                # ... Pass execution timing report ...
                if ('Pass execution timing report' in line):
#                    print 'Pass execution timing report'
                    line = inTimes.readline() # skip divider
                    line = inTimes.readline() # skip total exec time
                    line = inTimes.readline() # skip white space
                    
                    # get categories
                    line = inTimes.readline()
                    categories = getCategories(line)
                    
                    cont = True
                    while cont:
                        line = inTimes.readline().strip()
                        times = ''
                        if lineTest(line): cont=False
                        else: 
                            times = getTimes(line)
#                            writeTimes(categories, times)
                            insertTimes('Pass_execution_timing_report',categories, times)
                
                # Miscellaneous Ungrouped Timers
                if ('Miscellaneous Ungrouped Timers' in line):
#                    print 'Miscellaneous Ungrouped Timers'
                    line = inTimes.readline() # skip divider
                    line = inTimes.readline() # skip white space
                    
                    # get categories
                    line = inTimes.readline()
                    categories = getCategories(line)
                    
                    cont = True
                    while cont:
                        line = inTimes.readline().strip()
                        times = ''
                        if lineTest(line): cont=False
                        else: 
                            times = getTimes(line)
#                            writeTimes(categories, times)
                            insertTimes('Miscellaneous_Ungrouped_Timers',categories, times)
    
                if ('Execution times (seconds)' in line):
                    #print 'Execution times (seconds)'
                    cont = True
                    while cont:
                        line = inTimes.readline().strip()
                        times = ''
                        if lineTest(line): cont=False
                        else:
                            times = getTimesGCC(line)
#                            writeTimes(categories, times)
                            insertTimes('gcc', ['Name','User_Time','System_Time','Wall_Time'], times)

                if (line.startswith('# ')):
                    #print 'gcc -time'
                    times = getTimesGCC2(line)
                    insertTimes('gccTime', ['Name','User_Time','System_Time','Wall_Time'], times)
                    insertTimes('gccTime', ['Name','User_Time','System_Time','Wall_Time'], ["TOTAL"]+times[1:])

                if (line.startswith('MAOclang RUNTIME:') or line.startswith('AR RUNTIME:')):
                    times = getTimesOther(line)
                    insertTimes('other', ['Name','Wall_Time'], times)

            inTimes.close()
#            print "Done Parsing"
        writeTotals()
    except mdb.Error as e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    finally:
        if connection:
            connection.close()

def lineTest(line):
    #IS the start of a new dataset
    if not line:return True
    if isDivider(line):return True
    if line.startswith("==="):return True
    if line.startswith("# "):return True
    if line.startswith("MAOclang RUNTIME:"):return True
    if line.startswith("AR RUNTIME:"):return True
    if line.startswith("cc1plus: warning:"):return True
    if line.startswith("At global scope:"):return True
    return False

# get categories to dict
def getCategories(line):
    tmp = line.strip()
    tmp = re.sub(r'-','',tmp)
    tmp = re.sub(r'(?P<A>[^ ]+?) (?P<B>[^ ]+?)','\g<A>_\g<B>',tmp)
    tmp = re.sub(r'[+]','_',tmp)
    categories = tmp.split()
    return categories


# read times
def getTimes(line):
    tmp = line.strip()
    tmp = re.sub(r'\(.*?\)','',tmp)
#    tmp = re.sub(r'(?P<A>[a-zA-Z]+.*?) (?P<B>.*?)','\g<A>_\g<B>',tmp)
    times = tmp.split()
    return times

def getTimesGCC(line):
#    print line
    tmp = line.strip()
    tmp = re.sub(r'\(.*?\)','',tmp)
    tmp = re.sub(r':','',tmp)
    tmp = re.sub(r' (usr|sys|wall|ggc|kB)( |$)','',tmp)
    tmp = re.sub(r'(?P<A>[^ ]+?) (?P<B>[^ ]+?)','\g<A>_\g<B>',tmp)
    tmp = re.sub(r'(?P<A>[^ ]+?) (?P<B>[^ ]+?)','\g<A>_\g<B>',tmp)
#    tmp = re.sub(r'(?P<A>[a-zA-Z]+.*?) (?P<B>.*?)','\g<A>_\g<B>',tmp)
    times = tmp.split()
#    print times
    return times

def getTimesGCC2(line):
    #print line
    tmp = line.strip()
    times = tmp[2:].split()
    times += [str(float(times[1]) + float(times[2]))]
    #print times
    return times

def getTimesOther(line):
    #print line
    tmp = line.strip()
    times = tmp.split(':')
    #print times
    return times

# write times
def writeTimes(categories, times):
    col = ''
    data = ''
    for i in range(0,len(categories)):
        if (col != ''): col += ', '
        col += categories[i]

    for i in range(0,len(times)):
        if (data != ''): data += ', '
        data += times[i]
    print col +' ==> '+ data
        
def insertTimes(table, categories, times):
    global connection
    cur = connection.cursor()
    
    col = ''
    data = ''
    for i in range(0,len(categories)):
        if (col != ''): col += ', '
        col += "`" + categories[i] + "`"
        if (data != ''): data += ', '
        if (i == len(categories) -1):
            data += "'" + re.sub(r"\'","\\'",' '.join(times[i:])) + "'"
        else:
            data += "'" + times[i] + "'"
    
    execLine = """INSERT IGNORE INTO """ + table + """("""+ col +""") VALUES("""+ data +""")"""
#    print execLine
    cur.execute(execLine)

# bool isDivider "===-------------------------------------------------------------------------==="
def isDivider(line):
    if ("===-------------------------------------------------------------------------===" in line):
        return True
    else:
        return False



def cleanTables():
    global connection
    cur = connection.cursor()
    
    tables = ["Register_Allocation",
              "Instruction_Selection_and_Scheduling",
              "DWARF_Emission",
              "Pass_execution_timing_report",
              "Miscellaneous_Ungrouped_Timers",
              "gcc","gccTime","other"]
    
    for table in tables:
        cur.execute("""TRUNCATE TABLE """ + table)


def writeTotals():
    global connection
    cur = connection.cursor()
    
    tables = ["Register_Allocation",
              "Instruction_Selection_and_Scheduling",
              "DWARF_Emission",
              "Pass_execution_timing_report",
              "Miscellaneous_Ungrouped_Timers",
              "gcc","gccTime","other"]
    
    for table in tables:
        print "\n====== " + table + " ======\n"
        print "           {0}         |              {1}         |              {2}       |   {3}".format("Wall Time", "User Time", "System Time", "Name")
        cur.execute("""SELECT 
    `Name`,
    TRUNCATE(sum(`Wall_time`),4), 
    TRUNCATE(sum(`Wall_time`)/(SELECT sum(`Wall_Time`) FROM `"""+table+"""` WHERE `Name` = 'Total') *100, 2), 
    TRUNCATE(sum(`User_Time`),4), 
    TRUNCATE(sum(`User_Time`)/(SELECT sum(`User_Time`) FROM `"""+table+"""` WHERE `Name` = 'Total') *100, 2), 
    TRUNCATE(sum(`System_Time`),4), 
    TRUNCATE(sum(`System_Time`)/(SELECT sum(`System_Time`) FROM `"""+table+"""` WHERE `Name` = 'Total') *100, 2) 
FROM `"""+table+"""` 
GROUP BY `NAME` 
ORDER BY TRUNCATE(sum(`Wall_time`),4) DESC""")
        rows = cur.fetchall()
        for row in rows:
            name = row[0]
            wall = float(row[1])
            if row[2] is not None:
                wallP = float(row[2])
            else:
                wallP = 0.0
                
            user = float(row[3])
            if row[4] is not None:
                userP = float(row[4])
            else:
                userP = 0.0
                
            sys = float(row[5])
            if row[6] is not None:
                sysP = float(row[6])
            else:
                sysP = 0.0

            print "{0:10.4f}sec      {1:6.2f}%   |   {2:10.4f}sec      {3:6.2f}%   |   {4:10.4f}sec      {5:6.2f}%   |   {6}".format(wall, wallP, user, userP, sys, sysP, name)
            
        print "------------------------------------------------------------------------------------------------------------------------"
    
    

if __name__ == "__main__":
    main()
