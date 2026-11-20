#include "bbk7980.h"
extern bbk_u8 bbk_native_args[12];
extern void bbk_native_font(void);
bbk_u8 bbk_font_glyph(bbk_u16 code,bbk_u8 size,bbk_u8 *output) {
    bbk_u8 i;
    if(!output || (size!=12 && size!=16 && size!=24) ||
       (code>>8)<0x81 || (code>>8)>0xfe || (code&255)<0x40 ||
       (code&255)>0xfe || (code&255)==0x7f ||
       *(volatile bbk_u8 *)0x9eca==255)return 0;
    for(i=0;i<10;i++)bbk_native_args[i]=0;
    bbk_native_args[0]=(bbk_u8)code;bbk_native_args[1]=(bbk_u8)(code>>8);
    bbk_native_args[4]=(bbk_u8)(bbk_u16)output;
    bbk_native_args[5]=(bbk_u8)((bbk_u16)output>>8);
    bbk_native_args[6]=size;
    bbk_native_font();return 1;
}
bbk_u8 bbk_text_gbk(bbk_u8 x,bbk_u8 y,const char *text,bbk_u8 size,bbk_u8 shade) {
    bbk_u8 count=0,high,low;
    bbk_u16 code;
    static bbk_u8 glyph[72];
    if(!text || (size!=12 && size!=16 && size!=24))return 0;
    while((high=(bbk_u8)*text++)!=0) {
        low=(bbk_u8)*text++;
        if(high<0x81 || !low || (bbk_u16)x+size>240 || (bbk_u16)y+size>120)break;
        code=((bbk_u16)high<<8)|low;
        if(!bbk_font_glyph(code,size,glyph))break;
        bbk_mono(x,y,glyph,size,size,shade);x+=size;++count;
    }
    return count;
}
