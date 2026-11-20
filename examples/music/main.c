#include "bbk7980.h"
/* A newly authored ascending/descending C-major phrase, no external music file. */
const bbk_note tune[]={{262,16},{294,16},{330,16},{349,16},{392,16},{440,16},{494,16},{523,32},
    {0,8},{523,16},{494,16},{440,16},{392,16},{349,16},{330,16},{294,16},{262,32}};
volatile unsigned char playing,result,completed;
int main(void) {
    bbk_event event;
    bbk_fill(0,0,240,120,0);
    bbk_text_gbk(8,8,"\xd2\xf4\xc0\xd6\xd1\xdd\xca\xbe",16,3);
    bbk_text_gbk(8,32,"\xd6\xd0\xb6\xcf\xd5\xfd\xb3\xa3",12,2);
    while(bbk_event_wait(&event)) {
        if(event.type!=BBK_EVENT_KEY)continue;
        if(event.value==BBK_KEY_ESC)break;
        if(event.value==BBK_KEY_ENTER || event.value==BBK_KEY_SPACE) {
            bbk_fill(8,60,224,20,2);
            playing=1;result=bbk_music_play(tune,sizeof(tune)/sizeof(tune[0]),7);
            bbk_fill(8,60,224,20,1);
            if(!result)completed++;
            playing=0;
            if(result==BBK_KEY_HOME || result==BBK_KEY_ESC)break;
        }
    }
    bbk_keys_flush();return 0;
}
