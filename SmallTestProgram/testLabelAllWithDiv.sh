/usr/bin/clang -S -emit-llvm hellofunc.c -o hellofunc.bc
/usr/bin/clang -S -emit-llvm hellomake.c -o hellomake.bc
/usr/bin/llvm-link hellomake.bc hellofunc.bc -o hellomake.s.bc
/usr/bin/clang -S hellomake.s.bc -o hellomake.s

../bin/mao-x86_64-linux --mao=--plugin=../bin/MaoLabelAll-x86_64-linux.so:LABELALL:--plugin=../bin/MaoMOVToLEAAnnotate-x86_64-linux.so:MOVTOLEAA:--plugin=../bin/MaoNOPInsertionAnnotate-x86_64-linux.so:NOPINSERTIONA:ASM=o[hellomake_LA.a.s] hellomake.s

divanno -f hellomake_LA.a.s -o hellomake_LA.div.s -seed 15263748 -percent 30

gcc hellomake_LA.div.s -o hellomake
./hellomake
