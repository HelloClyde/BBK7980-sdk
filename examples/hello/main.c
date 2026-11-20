#include "bbk7980.h"
unsigned char x=112,y=66;
int main(void) {
    bbk_event event;
    bbk_fill(0,0,240,120,0);
    bbk_text_gbk(8,5,"\xbf\xaa\xb7\xa2\xd1\xdd\xca\xbe",16,3);
    bbk_text_gbk(8,25,"\xd6\xd0\xb6\xcf\xd5\xfd\xb3\xa3",12,2);
    bbk_fill(8,44,56,8,0);bbk_fill(64,44,56,8,1);
    bbk_fill(120,44,56,8,2);bbk_fill(176,44,56,8,3);
    bbk_fill(x,y,12,12,3);
    while(bbk_event_wait(&event)) {
        if(event.type!=BBK_EVENT_KEY)continue;
        if(event.value==BBK_KEY_ESC)break;
        bbk_fill(x,y,12,12,0);
        if(event.value==BBK_KEY_LEFT && x>=8)x-=8;
        if(event.value==BBK_KEY_RIGHT && x<=216)x+=8;
        if(event.value==BBK_KEY_UP && y>=64)y-=8;
        if(event.value==BBK_KEY_DOWN && y<=100)y+=8;
        bbk_fill(x,y,12,12,3);
    }
    bbk_keys_flush();return 0;
}
