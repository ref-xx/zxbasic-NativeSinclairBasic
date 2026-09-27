; ----------------------------------------------------------------
; Dynamic Jump & Restore linear search routine
; ----------------------------------------------------------------

    push namespace core

; ----------------------------------------------------------------
; __zxb_find_line:
; Linearly searches table in HL for first entry where entry.line >= DE.
; Table format: pairs of DW line_number, DW address.
; Sentinel: DW 0xFFFF, DW fallback_address.
; Input:  HL = pointer to table
;         DE = target line number (16-bit unsigned)
; Output: HL = resolved address
; Modifies: AF, BC, HL
; ----------------------------------------------------------------
__zxb_find_line:
__zxb_find_line_loop:
    ld c, (hl)
    inc hl
    ld b, (hl)
    inc hl                  ; BC = entry line number
    ld a, c
    sub e
    ld a, b
    sbc a, d                ; Carry clear (NC) if BC >= DE
    jr nc, __zxb_find_line_found
    inc hl
    inc hl                  ; Skip address word to next entry
    jr __zxb_find_line_loop

__zxb_find_line_found:
    ld a, (hl)
    inc hl
    ld h, (hl)
    ld l, a                 ; HL = target address
    ret

    pop namespace
