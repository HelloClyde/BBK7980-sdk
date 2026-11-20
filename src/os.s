.setcpu "65C02"
.export _bbk_event_wait, _bbk_event_translate, _bbk_keys_flush
.export _bbk_native_args, _bbk_native_font
.export _bbk_native_find, _bbk_native_size, _bbk_native_read, _bbk_native_result
.export _bbk_native_open, _bbk_native_write, _bbk_native_close, _bbk_native_seek, _bbk_native_delete
.export _bbk_native_key_poll
.export _bbk_native_idle
.import bbk_native_x, bbk_native_zp

.segment "BSS"
c_zp: .res 32
result: .res 1
_bbk_native_args: .res 12
_bbk_native_result: .res 4

.segment "CODE"
; Native foreground C uses the zero-page stack below X (normally $a0).
; cc65 owns $80..$9f. Keep two contexts; IRQ stack remains owned by the OS.
; No SEI/CLI or interrupt-enable-register writes in this bridge.
enter_os:
    ldy #31
save_c:
    lda $80,y
    sta c_zp,y
    lda bbk_native_zp,y
    sta $80,y
    dey
    bpl save_c
    ldx bbk_native_x
    rts
leave_os:
    sta result
    stx bbk_native_x
    ldy #31
save_os:
    lda $80,y
    sta bbk_native_zp,y
    lda c_zp,y
    sta $80,y
    dey
    bpl save_os
    lda result
    ldx #0
    rts

_bbk_event_wait:
    sta $09c3
    stx $09c4
    jsr enter_os
    jsr $86ee
    .word $410e
    .byte $02
    jmp leave_os
_bbk_event_translate:
    sta $09c3
    stx $09c4
    jsr enter_os
    jsr $86ee
    .word $4120
    .byte $02
    jmp leave_os
_bbk_keys_flush:
    jsr enter_os
    jsr $86ee
    .word $43a5
    .byte $02
    jmp leave_os
_bbk_native_font:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $40d2
    .byte $05
    jmp leave_os
set_args:
    ldy #11
font_args:
    lda _bbk_native_args,y
    sta $09c3,y
    dey
    bpl font_args
    lda $09c3
    rts
_bbk_native_find:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4024
    .byte $07
    jmp leave_os
_bbk_native_size:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4072
    .byte $03
    lda $00,x
    sta _bbk_native_result
    lda $01,x
    sta _bbk_native_result+1
    lda $02,x
    sta _bbk_native_result+2
    lda $03,x
    sta _bbk_native_result+3
    inx
    inx
    inx
    inx
    jmp leave_os
_bbk_native_read:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4072
    .byte $07
    jmp leave_os
_bbk_native_open:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4000
    .byte $07
    jmp leave_os
_bbk_native_write:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4112
    .byte $07
    jmp leave_os
_bbk_native_close:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4036
    .byte $07
    jmp leave_os
_bbk_native_seek:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4136
    .byte $07
    jmp leave_os
_bbk_native_delete:
    jsr enter_os
    jsr set_args
    jsr $86ee
    .word $4172
    .byte $07
    jmp leave_os
_bbk_native_key_poll:
    jsr enter_os
    jsr $86ee
    .word $43ab
    .byte $02
    lda $00,x
    sta _bbk_native_result
    lda $01,x
    sta _bbk_native_result+1
    inx
    inx
    jmp leave_os
_bbk_native_idle:
    ; ST2xxx WAI opcode, also used by the original fixed kernel at $8949.
    .byte $cb
    rts
