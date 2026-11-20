.setcpu "65C02"
.export __STARTUP__ : absolute = 1
.export bbk_native_x, bbk_native_zp
.import _main, zerobss, copydata
.importzp c_sp

.segment "NOINIT"
bbk_native_x: .res 1
bbk_native_zp: .res 32
bbk_c_stack: .res 2

.segment "STARTUP"
entry:
    ; Same banked context initializer as the original games.
    jsr $86ee
    .word $4108
    .byte $02
    ; Original games initialize this heap before allocating their work buffers.
    ; The NAND writer uses B000..BFFF, so a fixed C stack there is unsafe.
    stz $09c3
    lda #$c0
    sta $09c4
    lda #$f0
    sta $09c5
    lda #$3f
    sta $09c6
    jsr $86ee
    .word $4132
    .byte $02
    stz $09c3
    lda #$08
    sta $09c4
    jsr $86ee
    .word $4150
    .byte $02
    lda $00,x
    sta bbk_c_stack
    lda $01,x
    sta bbk_c_stack+1
    inx
    inx
    ora bbk_c_stack
    bne stack_ready
    rts
stack_ready:
    stx bbk_native_x
    php
    ldy #31
save_native:
    lda $80,y
    sta bbk_native_zp,y
    dey
    bpl save_native
    lda bbk_c_stack
    sta c_sp
    lda bbk_c_stack+1
    clc
    adc #$08
    sta c_sp+1
    jsr copydata
    jsr zerobss
    jsr _main
    ldy #31
restore_native:
    lda bbk_native_zp,y
    sta $80,y
    dey
    bpl restore_native
    ldx bbk_native_x
    lda bbk_c_stack
    sta $09c3
    lda bbk_c_stack+1
    sta $09c4
    jsr $86ee
    .word $4162
    .byte $02
    plp
    rts
