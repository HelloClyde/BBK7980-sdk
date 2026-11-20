#include "bbk7980.h"
#ifndef BBK_FRAMEBUFFER
#define BBK_FRAMEBUFFER ((volatile bbk_u8 *)0x0be0)
#endif
void bbk_pixel(bbk_u8 x,bbk_u8 y,bbk_u8 shade) {
    volatile bbk_u8 *p;
    bbk_u8 shift;
    if(x>=240 || y>=120)return;
    p=BBK_FRAMEBUFFER+(bbk_u16)y*60+(x>>2);shift=(3-(x&3))*2;
    *p=(*p&~(3<<shift))|((shade&3)<<shift);
}
void bbk_fill(bbk_u8 x,bbk_u8 y,bbk_u8 width,bbk_u8 height,bbk_u8 shade) {
    bbk_u16 right=(bbk_u16)x+width,bottom=(bbk_u16)y+height;
    bbk_u8 i,j,v=(shade&3)*85;
    volatile bbk_u8 *p;
    if(x>=240 || y>=120)return;
    if(right>240)right=240;if(bottom>120)bottom=120;
    for(j=y;j<bottom;j++) {
        i=x;
        while(i<right && (i&3))bbk_pixel(i++,j,shade);
        p=BBK_FRAMEBUFFER+(bbk_u16)j*60+(i>>2);
        while((bbk_u16)i+4<=right){*p++=v;i+=4;}
        while(i<right)bbk_pixel(i++,j,shade);
    }
}
void bbk_hline(bbk_u8 x,bbk_u8 y,bbk_u8 width,bbk_u8 shade){bbk_fill(x,y,width,1,shade);}
void bbk_vline(bbk_u8 x,bbk_u8 y,bbk_u8 height,bbk_u8 shade){bbk_fill(x,y,1,height,shade);}
void bbk_mono(bbk_u8 x,bbk_u8 y,const bbk_u8 *bits,bbk_u8 width,bbk_u8 height,bbk_u8 shade) {
    static const bbk_u8 masks[16]={0,3,12,15,48,51,60,63,192,195,204,207,240,243,252,255};
    bbk_u8 i,j,pitch=(width+7)/8;
    bbk_u8 b,mask,color=(shade&3)*85;
    bbk_u16 xx,yy;
    volatile bbk_u8 *p;
    if(!(x&3) && !(width&3) && (bbk_u16)x+width<=240 && (bbk_u16)y+height<=120) {
        p=BBK_FRAMEBUFFER+(bbk_u16)y*60+(x>>2);
        for(j=0;j<height;j++) {
            for(i=0;i<(width>>2);i++) {
                b=bits[i>>1];mask=masks[(i&1)?b&15:b>>4];
                p[i]=(p[i]&~mask)|(color&mask);
            }
            p+=60;bits+=pitch;
        }
        return;
    }
    for(j=0;j<height;j++)for(i=0;i<width;i++) {
        xx=(bbk_u16)x+i;yy=(bbk_u16)y+j;
        if(xx<240 && yy<120 && (bits[(bbk_u16)j*pitch+(i>>3)]&(128>>(i&7))))bbk_pixel((bbk_u8)xx,(bbk_u8)yy,shade);
    }
}
void bbk_glyph12(bbk_u8 x,bbk_u8 y,const bbk_u8 *bits,bbk_u8 count,bbk_u8 shade) {
    while(count-- && x<=228){bbk_mono(x,y,bits,12,12,shade);bits+=24;x+=12;}
}
void bbk_tile12(bbk_u8 x,bbk_u8 y,const bbk_u8 *bits,bbk_u8 selected) {
    static const bbk_u8 mask[36]={0,0,0,63,0,252,48,0,12,48,0,12,0,0,0,0,0,0,
        0,0,0,0,0,0,48,0,12,48,0,12,63,0,252,0,0,0};
    bbk_u8 row,col,v;
    volatile bbk_u8 *p;
    if(!(x&3) && x<=228 && y<=108) {
        p=BBK_FRAMEBUFFER+(bbk_u16)y*60+(x>>2);
        for(row=0;row<12;row++) {
            for(col=0;col<3;col++){v=*bits++;if(selected)v|=mask[row*3+col];p[col]=v;}
            p+=60;
        }
    } else {
        for(row=0;row<12;row++)for(col=0;col<12;col++) {
            v=bits[row*3+(col>>2)];if(selected)v|=mask[row*3+(col>>2)];
            if((bbk_u16)x+col<240 && (bbk_u16)y+row<120)bbk_pixel(x+col,y+row,(v>>(6-2*(col&3)))&3);
        }
    }
}
