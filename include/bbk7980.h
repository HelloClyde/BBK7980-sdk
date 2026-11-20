#ifndef BBK7980_H
#define BBK7980_H

#define BBK7980_SDK_VERSION "1.1.0"
#define BBK_WIDTH 240
#define BBK_HEIGHT 120
#define BBK_EVENT_KEY 1
#define BBK_EVENT_TEXT 2
#define BBK_EVENT_COMMAND 5
#define BBK_EVENT_PERIODIC 11
#define BBK_KEY_ESC 49
#define BBK_KEY_ENTER 50
#define BBK_KEY_HOME 52
#define BBK_KEY_LEFT 51
#define BBK_KEY_UP 57
#define BBK_KEY_RIGHT 58
#define BBK_KEY_DOWN 59
#define BBK_KEY_SPACE 34
#define BBK_KEY_F1 44
#define BBK_KEY_F2 45

typedef unsigned char bbk_u8;
typedef unsigned int bbk_u16;
typedef unsigned long bbk_u32;
typedef struct { bbk_u8 type; bbk_u16 value; } bbk_event;

/* Original V1.10 event pump. Interrupts stay enabled while waiting. */
bbk_u8 __fastcall__ bbk_event_wait(bbk_event *event);
bbk_u8 __fastcall__ bbk_event_translate(bbk_event *event);
void bbk_keys_flush(void);
/* Native system tick counter; a coherent snapshot, no interrupt masking. */
bbk_u32 bbk_ticks(void);
/* Read the system font file using its original glyph service. */
bbk_u8 bbk_font_glyph(bbk_u16 code,bbk_u8 size,bbk_u8 *output);
#define BBK_FILE_INVALID 255
#define BBK_READ_ERROR 65535U
#define BBK_IO_ERROR BBK_READ_ERROR
bbk_u8 __fastcall__ bbk_file_find(const char *gbk_filename);
bbk_u32 __fastcall__ bbk_file_size(bbk_u8 id);
/* Returns bytes read, zero at EOF, BBK_READ_ERROR on error. Maximum 32767. */
bbk_u16 bbk_file_read_at(bbk_u8 id,bbk_u32 offset,void *output,bbk_u16 length);
#define BBK_OPEN_READ 0
#define BBK_OPEN_REPLACE 1
#define BBK_OPEN_UPDATE 2
#define BBK_OPEN_CREATE 3
/* Stream handles (0..3) are distinct from directory file IDs. */
bbk_u8 bbk_file_open(const char *gbk_filename,bbk_u8 mode);
bbk_u16 bbk_file_write(bbk_u8 handle,const void *data,bbk_u16 length);
bbk_u8 __fastcall__ bbk_file_close(bbk_u8 handle);
bbk_u8 bbk_file_seek(bbk_u8 handle,bbk_u32 offset,bbk_u8 origin);
bbk_u8 __fastcall__ bbk_file_delete(const char *gbk_filename);
bbk_u8 bbk_file_error(void);
typedef struct { bbk_u16 hz; bbk_u16 ticks; } bbk_note;
/* Plays a RAM/ROM score using the native PSG, with IRQs enabled. 0=complete,
 * Esc/Home=cancel key, 255=bad score. ticks use the original OS tick counter. */
bbk_u8 bbk_music_play(const bbk_note *score,bbk_u8 count,bbk_u8 volume);

void bbk_pixel(bbk_u8 x,bbk_u8 y,bbk_u8 shade);
void bbk_fill(bbk_u8 x,bbk_u8 y,bbk_u8 width,bbk_u8 height,bbk_u8 shade);
void bbk_hline(bbk_u8 x,bbk_u8 y,bbk_u8 width,bbk_u8 shade);
void bbk_vline(bbk_u8 x,bbk_u8 y,bbk_u8 height,bbk_u8 shade);
void bbk_glyph12(bbk_u8 x,bbk_u8 y,const bbk_u8 *bits,bbk_u8 count,bbk_u8 shade);
void bbk_tile12(bbk_u8 x,bbk_u8 y,const bbk_u8 *bits,bbk_u8 selected);
void bbk_mono(bbk_u8 x,bbk_u8 y,const bbk_u8 *bits,bbk_u8 width,bbk_u8 height,bbk_u8 shade);
/* GBK double-byte text, sizes 12/16/24; returns glyphs drawn. */
bbk_u8 bbk_text_gbk(bbk_u8 x,bbk_u8 y,const char *text,bbk_u8 size,bbk_u8 shade);

#endif
