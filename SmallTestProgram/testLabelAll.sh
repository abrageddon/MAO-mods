/usr/bin/clang -S -emit-llvm hellofunc.c -o hellofunc.bc
/usr/bin/clang -S -emit-llvm hellomake.c -o hellomake.bc
/usr/bin/llvm-link hellomake.bc hellofunc.bc -o hellomake.s.bc
/usr/bin/clang -S hellomake.s.bc -o hellomake.s

../bin/mao-x86_64-linux --mao=--plugin=../bin/MaoLabelAll-x86_64-linux.so --mao=LABELALL=trace[3]:ASM=o[hellomake_LA.s] hellomake.s

gcc hellomake_LA.s -o hellomake
./hellomake
