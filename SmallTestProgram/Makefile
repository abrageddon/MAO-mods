CFLAGS+=-I. -g
DEPS = hellomake.h
OBJ = hellomake.o hellofunc.o 
ASS = hellomake.s hellofunc.s 
#CC = MAOclang.pyc
#CXX = MAOclang.pyc++
CC = clang
CXX = clang++

%.c: $(DEPS)

%.o: %.c
	$(CC) -c $(CFLAGS) $(CPPFLAGS) $< -o $@

hellomake: $(OBJ)
	$(CC) $(OBJ) -o $@

%.s: %.c
	$(CC) -S $(CFLAGS) $(CPPFLAGS) $< -o $@

assembly: $(ASS)
	

.PHONY: clean

clean:
	rm -f *.o hellomake

distclean:
	rm -f *.o *.s *.bc hellomake
