seed=$[ $RANDOM ]
percent=$[ $RANDOM % 100]
#percent=0


../bin/mao-x86_64-linux --mao=--plugin=../bin/MaoSchedRand-x86_64-linux.so --mao=SCHEDRAND=trace[3]+MultiCompilerSeed[${seed}]+ISchedRandPercentage[${percent}]:ASM=o[hellofunc_SchedRand.s] hellofunc.s

gcc -c hellofunc_SchedRand.s -o hellofunc.o
gcc -c hellomake.s -o hellomake.o
gcc hellomake.o hellofunc.o -o hellomake
./hellomake
