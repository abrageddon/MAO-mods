	.file	"hellomake.c"
	.text
	.globl	main
	.align	16, 0x90
	.type	main,@function
main:                                   # @main
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
	movl	$0, -4(%rbp)
	callq	myPrintHelloMake
	movl	$0, %eax
	addq	$16, %rsp
	popq	%rbp
	ret
.Ltmp6:
	.size	main, .Ltmp6-main
.Ltmp7:
	.cfi_endproc
.Leh_func_end0:


	.section	".note.GNU-stack","",@progbits
