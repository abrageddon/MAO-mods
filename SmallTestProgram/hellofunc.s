	.file	"hellofunc.c"
	.section	.rodata
.LC0:
	.string	"Hello makefiles!"
	.text
	.globl	myPrintHelloMake
	.type	myPrintHelloMake, @function
myPrintHelloMake:
.LFB0:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	movl	$.LC0, %edi
	call	puts
	nop
	popq	%rbp
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.size	myPrintHelloMake, .-myPrintHelloMake
	.ident	"GCC: (Ubuntu/Linaro 4.7.2-2ubuntu1) 4.7.2"
	.section	.note.GNU-stack,"",@progbits
