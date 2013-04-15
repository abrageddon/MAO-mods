	.file	"hellofunc.c"
	.text
	.globl	myPrintHelloMake
	.align	16, 0x90
	.type	myPrintHelloMake,@function
myPrintHelloMake:                       # @myPrintHelloMake
.Ltmp2:
	.cfi_startproc
# BB#0:
	pushq	%rbp
.Ltmp3:
	.cfi_def_cfa_offset 16
.Ltmp4:
	.cfi_offset %rbp, -16
	movq	%rsp, %rbp
.Ltmp5:
	.cfi_def_cfa_register %rbp
	subq	$16, %rsp
	leaq	.L.str, %rdi
	movb	$0, %al
	callq	printf
	movl	%eax, -4(%rbp)          # 4-byte Spill
	addq	$16, %rsp
	popq	%rbp
	ret
.Ltmp6:
	.size	myPrintHelloMake, .Ltmp6-myPrintHelloMake
.Ltmp7:
	.cfi_endproc
.Leh_func_end0:

	.type	.L.str,@object          # @.str
	.section	.rodata.str1.1,"aMS",@progbits,1
.L.str:
	.asciz	 "Hello makefiles!\n"
	.size	.L.str, 18


	.section	".note.GNU-stack","",@progbits
