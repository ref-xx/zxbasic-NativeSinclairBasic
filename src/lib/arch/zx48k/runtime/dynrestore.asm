; ----------------------------------------------------------------
; Dynamic Restore runtime for Boriel ZX Basic
; Implements RESTORE <expr>
; ----------------------------------------------------------------

#include once <read_restore.asm>
#include once <dynfindline.asm>

    push namespace core

; ----------------------------------------------------------------
; __DYN_RESTORE:
; Sets DATA pointer to first DATA line >= target line number in HL.
; ----------------------------------------------------------------
__DYN_RESTORE:
    ex de, hl               ; DE = target line number
    ld hl, .core.__ZXB_DYN_RESTORE_TABLE
    call __zxb_find_line
    jp __RESTORE

    pop namespace
