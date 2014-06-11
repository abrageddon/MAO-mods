includes="-I. -I/home/ubuntu/google-breakpad-read-only/src"
idStr="-Wl,--build-id=0xDECAFBAD"
breakpadlib="/home/ubuntu/google-breakpad-read-only/build/src/client/linux/libbreakpad_client.a"
link="-lpthread"
diversity="-Xclang -nop-insertion -mllvm -nop-insertion-percentage=100 -mllvm -sched-randomize -frandom-seed=12345"
#diversity="-frandom-seed=12345"
dwarf="-gdwarf-3"

multiclang.py++ $includes $diversity $breakpadlib $idStr $dwarf -c hellofunc.cpp -o hellofunc.o $link
multiclang.py++ $includes $diversity $breakpadlib $idStr $dwarf -c hellomake.cpp -o hellomake.o $link

#/usr/bin/llvm-link hellomake.bc hellofunc.bc -o hellomake.s.bc

#../bin/mao-x86_64-linux --mao=--plugin=../bin/MaoLabelAll-x86_64-linux.so --mao=LABELALL=trace[3]:ASM=o[hellomake_LA.s] hellomake.s

multiclang.py++ $diversity $breakpadlib $idStr $dwarf hellomake.o hellofunc.o -o hellomake $link
./hellomake
