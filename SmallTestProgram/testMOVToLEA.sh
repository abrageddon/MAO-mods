seed=$[ $RANDOM ]
percent=$[ $RANDOM % 100]


../bin/mao-x86_64-linux --mao=--plugin=../bin/MaoMOVToLEA-x86_64-linux.so --mao=MOVTOLEA=trace[3]+MultiCompilerSeed[${seed}]+MOVToLEAPercentage[${percent}]:ASM=o[hellofunc_MOVToLEA.s] hellofunc.s

gcc -c hellofunc_MOVToLEA.s -o hellofunc.o
gcc -c hellomake.s -o hellomake.o
gcc hellomake.o hellofunc.o -o hellomake
./hellomake
