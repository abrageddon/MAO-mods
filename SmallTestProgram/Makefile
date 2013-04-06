CFLAGS+=-I.
DEPS = hellomake.h
OBJ = hellomake.o hellofunc.o 
ASS = hellomake.s hellofunc.s 
CC = MAOclang
CXX = MAOclang++

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
