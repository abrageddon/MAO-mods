CFLAGS+=-I.
DEPS = hellomake.h
OBJ = hellomake.o hellofunc.o 
ASS = hellomake.s hellofunc.s 
CC = clang
CXX = clang++

%.c: $(DEPS)

%.o: %.c
	$(CC) -c $(CFLAGS) $(CPPFLAGS) $< -o $@

hellomake: $(OBJ)
	$(CC) $(OBJ) -flto -o $@

%.s: %.c
	$(CC) -S $(CFLAGS) $(CPPFLAGS) $< -o $@

assembly: $(ASS)
	

.PHONY: clean

clean:
	rm -f *.o hellomake

distclean:
	rm -f *.o *.s *.bc hellomake
