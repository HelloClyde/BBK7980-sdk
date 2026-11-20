/* PSG setup follows original bank 2:5507/54ea. Sequence and pacing are SDK code. */
#include "bbk7980.h"
#define PSG(a) (*(volatile bbk_u8 *)(a))
extern bbk_u8 bbk_native_result[4];
extern void bbk_native_key_poll(void);
extern void bbk_native_idle(void);

static void silence(void){PSG(0x17)=0;PSG(0x16)=0;}
bbk_u8 bbk_music_play(const bbk_note *score,bbk_u8 count,bbk_u8 volume) {
    bbk_u8 i,key=0;
    bbk_u16 reload,hz,duration,raw;
    bbk_u32 started;
    if(!score || !count || volume>15)return 255;
    for(i=0;i<count;i++)if((score[i].hz && score[i].hz<245) || score[i].hz>12000 || !score[i].ticks)return 255;
    for(i=0;i<count;i++) {
        hz=score[i].hz;duration=score[i].ticks;
        if(hz) {
            reload=4096U-(bbk_u16)(1000000UL/hz);
            /* Same two-channel tone mode and clock divider as the native beep. */
            PSG(0x16)=0;
            PSG(0x10)=(bbk_u8)reload;PSG(0x11)=(bbk_u8)(reload>>8);
            PSG(0x12)=(bbk_u8)reload;PSG(0x13)=(bbk_u8)(reload>>8);
            PSG(0x17)=volume|(volume<<4);PSG(0x16)=6;
        } else silence();
        started=bbk_ticks();
        do {
            bbk_native_key_poll();raw=bbk_native_result[0]|((bbk_u16)bbk_native_result[1]<<8);
            if(raw==BBK_KEY_ESC || raw==BBK_KEY_HOME){key=(bbk_u8)raw;goto done;}
            bbk_native_idle();
        } while((bbk_u32)(bbk_ticks()-started)<duration);
    }
done:
    silence();return key;
}
