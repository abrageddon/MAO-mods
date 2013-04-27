#!/bin/bash
while read line
  do echo "LINE: $line"
     export OIFS=$IFS
     export IFS=":"
     iter=0
     dir='TEST'
     cmd='TEST'

     for word in $line
      do if [ $iter == 0 ]
         then dir=$word
	     iter=1
	 else
	     cmd=${word:2}
	 fi
     done
     export IFS=$OIFS



     echo "DIR: $dir"
     echo "CMD: $cmd"
     (cd $dir && $cmd)
done <recorded.make
