' ----------------------------------------------------------------
' Sinclair BASIC compatible lightweight standalone INPUT routine
' Released under the MIT License
' ----------------------------------------------------------------
#ifndef __LIBRARY_SINCLAIR_INPUT__
#define __LIBRARY_SINCLAIR_INPUT__

#include once <pos.bas>
#include once <csrlin.bas>

#pragma push(case_insensitive)
#pragma case_insensitive = True

FUNCTION __zxb_input_str() AS STRING
    DIM LastK AS UBYTE AT 23560 : REM LAST_K system variable
    DIM result$ AS STRING
    DIM tmp AS UBYTE
    DIM x, y AS UBYTE

    tmp = PEEK 23611
    POKE 23611, PEEK 23611 bOR 8 : REM Set 'L' mode (letters/numbers)

    result$ = ""

    DO
        REM Draw cursor at current print position
        y = csrlin()
        x = pos()
        PRINT AT y, x; OVER 0; FLASH 1; "L"; AT y, x;

        REM Wait for a key press from 50Hz interrupt ISR
        LastK = 0
        DO LOOP UNTIL LastK <> 0

        REM Clear cursor
        PRINT AT y, x; OVER 0; FLASH 0; " "; AT y, x;

        IF LastK = 12 OR LastK = 8 THEN
            REM Delete / Backspace (Caps Shift + 0)
            IF LEN(result$) > 0 THEN
                IF LEN(result$) = 1 THEN
                    result$ = ""
                ELSE
                    result$ = result$( TO LEN(result$) - 2)
                END IF
                PRINT CHR$(8); " "; CHR$(8);
            END IF
        ELSEIF LastK >= 32 AND LastK < 127 THEN
            IF LEN(result$) < 255 THEN
                result$ = result$ + CHR$(LastK)
                PRINT CHR$(LastK);
            END IF
        END IF
    LOOP UNTIL LastK = 13 : REM Enter

    POKE 23611, tmp : REM Restore FLAGS
    PRINT "" : REM Move to next line

    RETURN result$
END FUNCTION

FUNCTION __zxb_input_num() AS FLOAT
    DIM s AS STRING
    s = __zxb_input_str()
    IF LEN(s) = 0 THEN
        RETURN 0
    END IF
    RETURN VAL(s)
END FUNCTION

#pragma pop(case_insensitive)

#endif
