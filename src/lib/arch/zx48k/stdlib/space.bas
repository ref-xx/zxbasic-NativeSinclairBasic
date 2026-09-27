' ----------------------------------------------------------------
' This file is released under the MIT License
'
' Copyleft (k) 2008
' by Jose Rodriguez-Rosa (a.k.a. Boriel) <http://www.boriel.com>
' ----------------------------------------------------------------

#ifndef __LIBRARY_SPACE__

REM Avoid recursive / multiple inclusion
#define __LIBRARY_SPACE__

#pragma push(case_insensitive)
#pragma case_insensitive = TRUE

' ----------------------------------------------------------------
' function SPACE$(n)
'
' Parameters:
'     n: number of spaces (Uinteger)
'
' Returns:
'     a string of n spaces (ASCII 32)
' ----------------------------------------------------------------
function fastcall space$(byval n as uinteger) as string
    asm
        push namespace core
        PROC
        LOCAL __SPACE_DONE

        ld a, h
        or l
        ret z       ; if n == 0, return NULL string (HL=0)

        push hl     ; save n
        inc hl
        inc hl      ; HL = n + 2
        ld b, h
        ld c, l
        call __MEM_ALLOC
        pop bc      ; BC = original n

        ld a, h
        or l
        ret z       ; return NULL if out of memory

        push hl     ; save start of string (to return in HL)

        ld (hl), c  ; store length low
        inc hl
        ld (hl), b  ; store length high
        inc hl      ; HL now points to 1st char

        ld (hl), 32 ; store first space
        dec bc      ; BC = n - 1
        ld a, b
        or c
        jr z, __SPACE_DONE ; if n == 1, done

        ld d, h
        ld e, l
        inc de      ; DE = HL + 1
        ldir        ; fill rest of spaces

__SPACE_DONE:
        pop hl      ; restore start of string for return
        ret

        ENDP
        pop namespace
    end asm
    n = n
    return ""
end function

#pragma pop(case_insensitive)

#endif
