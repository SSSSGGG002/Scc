.data
newline: .asciiz "\n"
str_s1: .asciiz "folded"
str_s2: .asciiz "broken"
str_s3: .asciiz "zero"
sym_x: .word 0
sym_y: .word 0
sym_t1: .word 0

.text
.globl main
main:
    #   0: (assign, -20, _, x)
    li $t0, -20
    sw $t0, sym_x
    #   1: (assign, 7, _, y)
    li $t0, 7
    sw $t0, sym_y
    #   2: (bgt, x, -20, L1)
    lw $t0, sym_x
    li $t1, -20
    bgt $t0, $t1, L1
    #   3: (write, s1, string, _)
    la $a0, str_s1
    li $v0, 4
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    #   4: (goto, _, _, L2)
    j L2
    #   5: (label, _, _, L1)
L1:
    #   6: (write, s2, string, _)
    la $a0, str_s2
    li $v0, 4
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    #   7: (label, _, _, L2)
L2:
    #   8: (beq, y, 0, L3)
    lw $t0, sym_y
    li $t1, 0
    beq $t0, $t1, L3
    #   9: (write, y, integer, _)
    lw $a0, sym_y
    li $v0, 1
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    #  10: (goto, _, _, L4)
    j L4
    #  11: (label, _, _, L3)
L3:
    #  12: (write, s3, string, _)
    la $a0, str_s3
    li $v0, 4
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    #  13: (label, _, _, L4)
L4:
    #  14: (label, _, _, L5)
L5:
    #  15: (bge, x, y, L6)
    lw $t0, sym_x
    lw $t1, sym_y
    bge $t0, $t1, L6
    #  16: (add, x, 5, t1)
    lw $t0, sym_x
    li $t1, 5
    add $t2, $t0, $t1
    sw $t2, sym_t1
    #  17: (assign, t1, _, x)
    lw $t0, sym_t1
    sw $t0, sym_x
    #  18: (goto, _, _, L5)
    j L5
    #  19: (label, _, _, L6)
L6:
    #  20: (write, x, integer, _)
    lw $a0, sym_x
    li $v0, 1
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    li $v0, 10
    syscall
