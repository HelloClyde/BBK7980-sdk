#include "bbk7980.h"
extern bbk_u8 bbk_native_args[12],bbk_native_result[4];
extern bbk_u8 bbk_native_find(void),bbk_native_read(void);
extern void bbk_native_size(void);
extern bbk_u8 bbk_native_open(void),bbk_native_write(void),bbk_native_close(void);
extern bbk_u8 bbk_native_seek(void),bbk_native_delete(void);
static char filename_ram[64];
static bbk_u8 write_buffer[128],last_error;
static bbk_u8 create_attributes[8];
bbk_u8 bbk_stream_access[4];
static bbk_u8 filename_args(const char *filename) {
    bbk_u8 i=0;
    if(!filename || !*filename)return BBK_FILE_INVALID;
    while(filename[i] && i<63){filename_ram[i]=filename[i];++i;}
    if(filename[i])return BBK_FILE_INVALID;
    filename_ram[i]=0;
    /* ROM literals live in the app's PRR window, switched by the bank bridge. */
    bbk_native_args[0]=(bbk_u8)(bbk_u16)filename_ram;
    bbk_native_args[1]=(bbk_u8)((bbk_u16)filename_ram>>8);
    return 0;
}
bbk_u8 __fastcall__ bbk_file_find(const char *filename) {
    bbk_u8 id;
    if(filename_args(filename)){last_error=255;return BBK_FILE_INVALID;}
    id=bbk_native_find();last_error=*(volatile bbk_u8 *)0x96b7;return id;
}
bbk_u32 __fastcall__ bbk_file_size(bbk_u8 id) {
    bbk_u16 ptr;
    if(id==BBK_FILE_INVALID){last_error=255;return 0xffffffffUL;}
    /* Same file-ID directory entry selection used by native bank 7:6d92. */
    ptr=0x98c7U+(bbk_u16)id*109U;
    bbk_native_args[0]=(bbk_u8)ptr;bbk_native_args[1]=(bbk_u8)(ptr>>8);
    bbk_native_size();
    last_error=*(volatile bbk_u8 *)0x96b7;
    return (bbk_u32)bbk_native_result[0]|((bbk_u32)bbk_native_result[1]<<8)|
           ((bbk_u32)bbk_native_result[2]<<16)|((bbk_u32)bbk_native_result[3]<<24);
}
bbk_u16 bbk_file_read_at(bbk_u8 id,bbk_u32 offset,void *output,bbk_u16 length) {
    bbk_u32 size=bbk_file_size(id);
    if(size==0xffffffffUL || !output || length>32767U){last_error=255;return BBK_READ_ERROR;}
    if(offset>=size || !length){last_error=0;return 0;}
    if(size-offset<length)length=(bbk_u16)(size-offset);
    bbk_native_args[0]=id;
    bbk_native_args[1]=(bbk_u8)offset;bbk_native_args[2]=(bbk_u8)(offset>>8);
    bbk_native_args[3]=(bbk_u8)(offset>>16);bbk_native_args[4]=(bbk_u8)(offset>>24);
    bbk_native_args[5]=(bbk_u8)(bbk_u16)output;
    bbk_native_args[6]=(bbk_u8)((bbk_u16)output>>8);
    bbk_native_args[7]=(bbk_u8)length;bbk_native_args[8]=(bbk_u8)(length>>8);
    last_error=bbk_native_read();if(last_error)return BBK_READ_ERROR;
    return length;
}
bbk_u8 bbk_file_open(const char *filename,bbk_u8 mode) {
    bbk_u8 handle;
    /* Native mode 1 preserves the old size. Implement truncate/create using
     * the original unlink + exclusive-create functions, like a new data file. */
    if(mode==BBK_OPEN_REPLACE) {
        handle=bbk_file_find(filename);
        if(handle!=255){if(bbk_file_delete(filename))return 255;}
        else if(last_error!=1)return 255;
        mode=BBK_OPEN_CREATE;
    }
    if(mode>3 || filename_args(filename)){last_error=255;return 255;}
    bbk_native_args[2]=mode;
    /* The final native argument is a POINTER to eight metadata bytes, not flags.
     * This matches the all-zero data-file attributes used by stock UART upload. */
    bbk_native_args[3]=(bbk_u8)(bbk_u16)create_attributes;
    bbk_native_args[4]=(bbk_u8)((bbk_u16)create_attributes>>8);
    handle=bbk_native_open();last_error=*(volatile bbk_u8 *)0x96b7;
    if(handle<4)bbk_stream_access[handle]=mode==BBK_OPEN_READ?1:mode==BBK_OPEN_UPDATE?3:2;
    return handle;
}
bbk_u16 bbk_file_write(bbk_u8 handle,const void *data,bbk_u16 length) {
    const bbk_u8 *source=data;
    bbk_u16 done=0;
    bbk_u8 n,i;
    if(handle>=4 || (!data && length) || length>32767U){last_error=255;return BBK_READ_ERROR;}
    if(!(bbk_stream_access[handle]&2)){last_error=6;return BBK_READ_ERROR;}
    while(done<length) {
        n=(length-done)>128?128:(bbk_u8)(length-done);
        for(i=0;i<n;i++)write_buffer[i]=source[done+i];
        bbk_native_args[0]=handle;
        bbk_native_args[1]=(bbk_u8)(bbk_u16)write_buffer;
        bbk_native_args[2]=(bbk_u8)((bbk_u16)write_buffer>>8);
        bbk_native_args[3]=n;bbk_native_args[4]=0;
        last_error=bbk_native_write();
        if(last_error)return BBK_READ_ERROR;
        done+=n;
    }
    last_error=0;return done;
}
bbk_u8 __fastcall__ bbk_file_close(bbk_u8 handle) {
    if(handle>=4 || !bbk_stream_access[handle]){last_error=7;return 7;}
    bbk_native_args[0]=handle;last_error=bbk_native_close();bbk_stream_access[handle]=0;return last_error;
}
bbk_u8 bbk_file_seek(bbk_u8 handle,bbk_u32 offset,bbk_u8 origin) {
    if(handle>=4 || !bbk_stream_access[handle] || origin>2){last_error=255;return 255;}
    bbk_native_args[0]=handle;
    bbk_native_args[1]=(bbk_u8)offset;bbk_native_args[2]=(bbk_u8)(offset>>8);
    bbk_native_args[3]=(bbk_u8)(offset>>16);bbk_native_args[4]=(bbk_u8)(offset>>24);
    /* Native seek code 255 means backwards from EOF; code 2 is backwards from
     * the current position. Public origin 2 is EOF, offset is a backwards gap. */
    bbk_native_args[5]=origin==2?255:origin;last_error=bbk_native_seek();return last_error;
}
bbk_u8 __fastcall__ bbk_file_delete(const char *filename) {
    if(filename_args(filename)){last_error=255;return 255;}
    bbk_native_delete();last_error=*(volatile bbk_u8 *)0x96b7;return last_error;
}
bbk_u8 bbk_file_error(void){return last_error;}
