	.code64		# id: 0, l: 0	
	.file	"hellofunc.c"	# id: 1, l: 1	
	.section	.text	# id: 2, l: 2	
	.globl	myPrintHelloMake	# id: 3, l: 3	
	.p2align	4, 144, 0	# id: 4, l: 4	
	.type	myPrintHelloMake, @function	# id: 5, l: 5	
myPrintHelloMake:	# id: 6, l: 6	
.Ltmp2:	# id: 7, l: 7	
	.cfi_startproc		# id: 8, l: 8	
	pushq	%rbp	# id: 9, l: 10	
.Ltmp3:	# id: 10, l: 11	
	.cfi_def_cfa_offset	16	# id: 11, l: 12	
.Ltmp4:	# id: 12, l: 13	
	.cfi_offset	%rbp, -16	# id: 13, l: 14	
	movq	%rsp, %rbp	# id: 14, l: 15	
.Ltmp5:	# id: 15, l: 16	
	.cfi_def_cfa_register	%rbp	# id: 16, l: 17	
	subq	$16, %rsp	# id: 17, l: 18	
	nop		# id: 36, l: 0	
	leaq	.L.str, %rdi	# id: 18, l: 19	
	movb	$0, %al	# id: 19, l: 20	
	callq	printf	# id: 20, l: 21	
	movl	%eax, -4(%rbp)	# id: 21, l: 22	
	addq	$16, %rsp	# id: 22, l: 23	
	popq	%rbp	# id: 23, l: 24	
	ret		# id: 24, l: 25	
.Ltmp6:	# id: 25, l: 26	
	.size	myPrintHelloMake, .Ltmp6-myPrintHelloMake	# id: 26, l: 27	
.Ltmp7:	# id: 27, l: 28	
	.cfi_endproc		# id: 28, l: 29	
.Leh_func_end0:	# id: 29, l: 30	
	.type	.L.str, @object	# id: 30, l: 32	
	.section	.rodata.str1.1, "aMS",@progbits,1	# id: 31, l: 33	
.L.str:	# id: 32, l: 34	
	.string	"Hello makefiles!\n"	# id: 33, l: 35	
	.size	.L.str, 18	# id: 34, l: 36	
	.section	.note.GNU-stack, "",@progbits	# id: 35, l: 39	
