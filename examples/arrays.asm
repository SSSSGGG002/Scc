.data
newline: .asciiz "\n"
bounds_error_msg: .asciiz "Array index out of bounds\n"
.align 2
sym_nums: .space 16
sym_i: .word 0
sym_total: .word 0
sym_t1: .word 0
sym_t2: .word 0
sym_t3: .word 0

.text
.globl main
main:
    #   0: (assign, 3, _, nums[0])
    li $t0, 3
    li $t8, 0
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    sw $t0, 0($t9)
    #   1: (assign, 4, _, nums[1])
    li $t0, 4
    li $t8, 1
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    sw $t0, 0($t9)
    #   2: (add, nums[0], nums[1], t1)
    li $t8, 0
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    lw $t0, 0($t9)
    li $t8, 1
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    lw $t1, 0($t9)
    add $t2, $t0, $t1
    sw $t2, sym_t1
    #   3: (assign, t1, _, nums[2])
    lw $t0, sym_t1
    li $t8, 2
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    sw $t0, 0($t9)
    #   4: (assign, 10, _, nums[3])
    li $t0, 10
    li $t8, 3
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    sw $t0, 0($t9)
    #   5: (assign, 0, _, i)
    li $t0, 0
    sw $t0, sym_i
    #   6: (assign, 0, _, total)
    li $t0, 0
    sw $t0, sym_total
    #   7: (label, _, _, L1)
L1:
    #   8: (bge, i, 4, L2)
    lw $t0, sym_i
    li $t1, 4
    bge $t0, $t1, L2
    #   9: (add, total, nums[i], t2)
    lw $t0, sym_total
    lw $t8, sym_i
    bltz $t8, runtime_bounds_error
    li $t7, 4
    bge $t8, $t7, runtime_bounds_error
    sll $t8, $t8, 2
    la $t9, sym_nums
    add $t9, $t9, $t8
    lw $t1, 0($t9)
    add $t2, $t0, $t1
    sw $t2, sym_t2
    #  10: (assign, t2, _, total)
    lw $t0, sym_t2
    sw $t0, sym_total
    #  11: (add, i, 1, t3)
    lw $t0, sym_i
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, sym_t3
    #  12: (assign, t3, _, i)
    lw $t0, sym_t3
    sw $t0, sym_i
    #  13: (goto, _, _, L1)
    j L1
    #  14: (label, _, _, L2)
L2:
    #  15: (write, total, integer, _)
    lw $a0, sym_total
    li $v0, 1
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    li $v0, 10
    syscall

runtime_bounds_error:
    la $a0, bounds_error_msg
    li $v0, 4
    syscall
    li $v0, 10
    syscall
