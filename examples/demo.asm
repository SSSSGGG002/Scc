.data
newline: .asciiz "\n"
sym_x: .word 0
sym_y: .word 0
sym_c: .word 0
sym_t1: .word 0
sym_t2: .word 0

.text
.globl main
main:
    #   0: (read, integer, _, x)
    li $v0, 5
    syscall
    sw $v0, sym_x
    #   1: (add, x, 10, t1)
    lw $t0, sym_x
    li $t1, 10
    add $t2, $t0, $t1
    sw $t2, sym_t1
    #   2: (assign, t1, _, y)
    lw $t0, sym_t1
    sw $t0, sym_y
    #   3: (assign, 65, _, c)
    li $t0, 65
    sw $t0, sym_c
    #   4: (bge, y, 20, L1)
    lw $t0, sym_y
    li $t1, 20
    bge $t0, $t1, L1
    #   5: (write, y, integer, _)
    lw $a0, sym_y
    li $v0, 1
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    #   6: (goto, _, _, L2)
    j L2
    #   7: (label, _, _, L1)
L1:
    #   8: (write, c, char, _)
    lw $a0, sym_c
    li $v0, 11
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    #   9: (label, _, _, L2)
L2:
    #  10: (label, _, _, L3)
L3:
    #  11: (bge, x, y, L4)
    lw $t0, sym_x
    lw $t1, sym_y
    bge $t0, $t1, L4
    #  12: (add, x, 1, t2)
    lw $t0, sym_x
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, sym_t2
    #  13: (assign, t2, _, x)
    lw $t0, sym_t2
    sw $t0, sym_x
    #  14: (goto, _, _, L3)
    j L3
    #  15: (label, _, _, L4)
L4:
    #  16: (write, x, integer, _)
    lw $a0, sym_x
    li $v0, 1
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    li $v0, 10
    syscall
