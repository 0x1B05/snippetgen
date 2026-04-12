.section entry, "ax"
.globl _start
.type _start, @function

#define MSTATUS_FS 0x00006000
#define MSTATUS_VS 0x00000600
#define STKSHIFT 17

_start:
  mv s0, zero
  li a0, MSTATUS_FS | MSTATUS_VS
  csrs mstatus, a0
  csrwi fcsr, 0

  csrr a0, mhartid
  la tp, _stack_top
  addi sp, a0, 1
  slli sp, sp, STKSHIFT
  add sp, sp, tp
  slli a2, a0, STKSHIFT
  add tp, tp, a2

  call main
1:
  .word 0x0005006b
  j 1b
