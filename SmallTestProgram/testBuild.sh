seed=$[ $RANDOM ]
percent=$[ $RANDOM % 100]


../bin/mao-x86_64-linux --mao=--plugin=../bin/MaoNOPInsertion-x86_64-linux.so --mao=NOPINSERTION=trace[3]+MultiCompilerSeed[${seed}]+NOPInsertionPercentage[${percent}]:ASM=o[hellofunc_NOP.s] hellofunc.s

gcc -c hellofunc_NOP.s -o hellofunc.o
gcc -c hellomake.s -o hellomake.o
gcc hellomake.o hellofunc.o -o hellomake
./hellomake
