; ----------------------------------------------------------------
; Dynamic Jump runtime for Boriel ZX Basic
; Implements GO TO <expr> and GO SUB <expr>
; ----------------------------------------------------------------

#include once <dynfindline.asm>

    push namespace core

; ----------------------------------------------------------------
; __DYN_GOTO:
; Jumps to the first line >= target line number in HL.
; Discards caller return address so stack is clean.
; ----------------------------------------------------------------
__DYN_GOTO:
    pop bc                  ; Discard caller return address
    ex de, hl               ; DE = target line number
    ld hl, .core.__ZXB_DYN_JUMP_TABLE
    call __zxb_find_line
    jp (hl)

; ----------------------------------------------------------------
; __DYN_GOSUB:
; Calls subroutine at first line >= target line number in HL.
; Retains caller return address on top of stack.
; Subroutine RETURN (ret) returns directly to caller.
; ----------------------------------------------------------------
__DYN_GOSUB:
    ex de, hl               ; DE = target line number
    ld hl, .core.__ZXB_DYN_JUMP_TABLE
    call __zxb_find_line
    jp (hl)

    pop namespace
