.data
newline: .asciiz "\n"
.align 2
sym_x: .word 0
ptr_bump__step: .word 0
ptr_bump__target: .word 0
arg_bump__step: .word 0
arg_bump__target: .word 0
sym_bump__twice__t1: .word 0

.text
.globl main
main:
    #   0: (assign, 1, _, x)
    li $t0, 1
    sw $t0, sym_x
    #   1: (param, 2, _, bump__step)
    li $t0, 2
    sw $t0, arg_bump__step
    #   2: (param_ref, &x, _, bump__target)
    la $t0, sym_x
    sw $t0, arg_bump__target
    #   3: (call, _, _, bump)
    jal proc_bump
    #   4: (write, x, integer, _)
    lw $a0, sym_x
    li $v0, 1
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    li $v0, 10
    syscall

    #   5: (proc, _, _, bump)
proc_bump:
    addi $sp, $sp, -16
    sw $ra, 0($sp)
    lw $t0, ptr_bump__step
    sw $t0, 4($sp)
    addi $t1, $sp, 12
    sw $t1, ptr_bump__step
    lw $t2, arg_bump__step
    sw $t2, 0($t1)
    lw $t0, ptr_bump__target
    sw $t0, 8($sp)
    lw $t1, arg_bump__target
    sw $t1, ptr_bump__target
    #   6: (call, _, _, bump__twice)
    jal proc_bump__twice
    #   7: (call, _, _, bump__twice)
    jal proc_bump__twice
    #   8: (endproc, _, _, bump)
end_proc_bump:
    lw $t0, 4($sp)
    sw $t0, ptr_bump__step
    lw $t0, 8($sp)
    sw $t0, ptr_bump__target
    lw $ra, 0($sp)
    addi $sp, $sp, 16
    jr $ra
    #   9: (proc, _, _, bump__twice)
proc_bump__twice:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    #  10: (add, bump__target, bump__step, bump__twice__t1)
    lw $t9, ptr_bump__target
    lw $t0, 0($t9)
    lw $t9, ptr_bump__step
    lw $t1, 0($t9)
    add $t2, $t0, $t1
    sw $t2, sym_bump__twice__t1
    #  11: (assign, bump__twice__t1, _, bump__target)
    lw $t0, sym_bump__twice__t1
    lw $t9, ptr_bump__target
    sw $t0, 0($t9)
    #  12: (endproc, _, _, bump__twice)
end_proc_bump__twice:
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra
