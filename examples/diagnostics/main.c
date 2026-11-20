#include "bbk7980.h"
/* Exported symbols make emulator validation read-only and deterministic. */
volatile unsigned char sdk_ready, event_count, last_type;
volatile unsigned int last_value;
volatile unsigned int translated_value;
volatile unsigned char translated_type;
volatile unsigned char last_key, key_count, periodic_count, font_ok;
volatile unsigned long started, latest;
unsigned char font_buffer[128],file_buffer[600];
volatile unsigned char file_id,missing_id;
volatile unsigned int file_read;
volatile unsigned long file_size;
volatile unsigned char file_edges_ok,canary_ok;
unsigned char edge_buffer[8];
volatile unsigned int stress_sum;
unsigned char initialized_data=0x5a;
unsigned char initialized_array[4]={1,3,5,7};
int main(void) {
    bbk_event event;
    unsigned int i,sum=0;
    started=bbk_ticks();
    sdk_ready=initialized_data==0x5a && initialized_array[3]==7;
    font_ok=bbk_font_glyph(0xd6d0,12,font_buffer);
    if(bbk_font_glyph(0xd6d0,16,font_buffer+24))font_ok|=2;
    if(bbk_font_glyph(0xd6d0,24,font_buffer+56))font_ok|=4;
    file_id=bbk_file_find("font.bin");missing_id=bbk_file_find("missing-file.bin");
    file_size=bbk_file_size(file_id);
    file_read=bbk_file_read_at(file_id,500,file_buffer,600);
    file_edges_ok=bbk_file_read_at(file_id,file_size-6,edge_buffer,8)==6 &&
        bbk_file_read_at(file_id,file_size,edge_buffer,8)==0 &&
        bbk_file_read_at(255,0,edge_buffer,8)==BBK_READ_ERROR;
    for(i=0;i<10000;++i)sum+=(i^0x5a5aU);
    stress_sum=sum;
    canary_ok=initialized_data==0x5a && initialized_array[0]==1 && initialized_array[3]==7;
    while(1) {
        if(!bbk_event_wait(&event))continue;
        ++event_count;last_type=event.type;last_value=event.value;
        if(event.type==BBK_EVENT_KEY){
            last_key=(unsigned char)event.value;++key_count;
            bbk_event_translate(&event);translated_value=event.value;translated_type=event.type;
        }
        if(event.type==BBK_EVENT_PERIODIC)++periodic_count;
        latest=bbk_ticks();
        if(last_type==BBK_EVENT_KEY && (last_key==BBK_KEY_ESC || last_key==BBK_KEY_HOME))break;
    }
    bbk_keys_flush();
    return 0;
}
