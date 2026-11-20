#include "bbk7980.h"
bbk_u32 bbk_ticks(void) {
    volatile const bbk_u8 *p=(const bbk_u8 *)0xa44c;
    bbk_u8 a,b,c,d;
    /* High-to-low/high recheck avoids torn carries without stopping IRQs. */
    do { d=p[3];c=p[2];b=p[1];a=p[0]; }
    while(d!=p[3] || c!=p[2] || b!=p[1]);
    return ((bbk_u32)d<<24)|((bbk_u32)c<<16)|((bbk_u16)b<<8)|a;
}
