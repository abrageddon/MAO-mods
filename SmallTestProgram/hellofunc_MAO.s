	.code64		# id: 0, l: 0	
	.file	"hellofunc.c"	# id: 1, l: 1	
	.section	.rodata	# id: 2, l: 2	
.LC0:	# id: 3, l: 3	
	.string	"Hello makefiles!"	# id: 4, l: 4	
	.section	.text	# id: 5, l: 5	
	.globl	myPrintHelloMake	# id: 6, l: 6	
	.type	myPrintHelloMake, @function	# id: 7, l: 7	
myPrintHelloMake:	# id: 8, l: 8	
.LFB0:	# id: 9, l: 9	
	.cfi_startproc		# id: 10, l: 10	
	pushq	%rbp	# id: 11, l: 11	
	.cfi_def_cfa_offset	16	# id: 12, l: 12	
	.cfi_offset	6, -16	# id: 13, l: 13	
	movq	%rsp, %rbp	# id: 14, l: 14	
	.cfi_def_cfa_register	6	# id: 15, l: 15	
	movl	$.LC0, %edi	# id: 16, l: 16	
	call	puts	# id: 17, l: 17	
	nop		# id: 18, l: 18	
	popq	%rbp	# id: 19, l: 19	
	.cfi_def_cfa	7, 8	# id: 20, l: 20	
	ret		# id: 21, l: 21	
	.cfi_endproc		# id: 22, l: 22	
.LFE0:	# id: 23, l: 23	
	.size	myPrintHelloMake, .-myPrintHelloMake	# id: 24, l: 24	
	.ident	"GCC: (Ubuntu/Linaro 4.7.2-2ubuntu1) 4.7.2"	# id: 25, l: 25	
	.section	.note.GNU-stack, "",@progbits	# id: 26, l: 26	
