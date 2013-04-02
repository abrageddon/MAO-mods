gcc -c hellofunc_NOP.s -o hellofunc.o
gcc -c hellomake.s -o hellomake.o
gcc hellomake.o hellofunc.o -o hellomake
