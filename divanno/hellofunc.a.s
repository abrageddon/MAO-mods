	.code64	
	.file	"hellofunc.c"
	.section	.text
	.globl	myPrintHelloMake
	.p2align	4, 144, 0
	.type	myPrintHelloMake, @function
myPrintHelloMake:
.Ltmp2:
	.cfi_startproc	
	pushq %rbp	# MC=N
.Ltmp3:
	.cfi_def_cfa_offset	16
.Ltmp4:
	.cfi_offset	%rbp, -16
	movq %rsp,%rbp	# MC=NM  #
.Ltmp5:
	.cfi_def_cfa_register	%rbp
	subq $16,%rsp	# MC=N
	leaq .L.str,%rdi	# MC=N  #
	movb $0,%al	# MC=N
	callq printf	# MC=N
	movl %eax,-4(%rbp)	# MC=N
	addq $16,%rsp	# MC=N
	popq %rbp	# MC=N
	ret	# MC=N
.Ltmp6:
	.size	myPrintHelloMake, .Ltmp6-myPrintHelloMake
.Ltmp7:
	.cfi_endproc	
.Leh_func_end0:
	.type	.L.str, @object
	.section	.rodata.str1.1, "aMS",@progbits,1
.L.str:
	.string	"Hello makefiles!\n"
	.size	.L.str, 18
	.section	.note.GNU-stack, "",@progbits
