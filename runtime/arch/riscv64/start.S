.section .bss.stack, "aw", @nobits
.align 12
.globl xsrt_boot_stack
xsrt_boot_stack:
  .space 4096
.globl xsrt_boot_stack_top
xsrt_boot_stack_top:

.section .text.start
.globl _start
_start:
  la sp, xsrt_boot_stack_top
  call main
1:
  j 1b
