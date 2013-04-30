#!/bin/bash
while read line
  do #echo -e "\nLINE: $line"
     echo ""
     export OIFS=$IFS
     export IFS=":"
     iter=0
     dir='TEST'
     cmd=''

     for word in $line
      do if [ $iter == 0 ]
         then dir=$word
	     iter=1
             export IFS=$OIFS
	 elif [ $iter == 1 ]
	 then
	     #Clobbers lines with : in them 
	     #echo "WORD: $word"
	     cmd="${word}"
	     iter=2
	 else
	     #echo "CMD: $cmd"
	     #echo "WORD: $word"
	     cmd="${cmd}:${word}"
	     #echo "RESULT: $cmd"
	 fi
     done
     export IFS=$OIFS

     cmd="${cmd:3}"
#skip make lines that start with make.... or make make be null?!
#:-c /usr/bin/make
     if [[ "$cmd" == /usr/bin/make* ]]
     then
       echo "===== MAKE: $dir"
       continue
     fi

     echo "DIR: $dir"
     echo "CMD: $cmd"

     #echo $cmd | sed 's/(/\\(/g'  | sed 's/)/\\)/g'  | sed 's/"/\\"/g' > /tmp/run.sh
     echo $cmd > /tmp/run.sh
     (cd $dir && (sh /tmp/run.sh))
     retVal=$?

     if [ $retVal -ne 0 ]
     then 
        echo $cmd | sed 's/(/\\(/g'  | sed 's/)/\\)/g'  | sed 's/"/\\"/g' > /tmp/run.sh
        echo "ERROR: $cmd"
        (cd $dir && (sh /tmp/run.sh))
	retVal=$?

	if [ $retVal -ne 0 ]
	then 
            exit $retVal
	fi
     fi

done <recorded.make
