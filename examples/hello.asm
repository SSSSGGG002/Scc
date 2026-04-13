.data
newline: .asciiz "\n"
str_s1: .asciiz "Hello"

.text
.globl main
main:
    #   0: (write, s1, string, _)
    la $a0, str_s1
    li $v0, 4
    syscall
    la $a0, newline
    li $v0, 4
    syscall
    li $v0, 10
    syscall
