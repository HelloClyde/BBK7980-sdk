/* Original Minesweeper rules, GPL-3.0-or-later. Shared by native and host tests. */
#include "game.h"

static unsigned short random16(Game *g) {
    unsigned short x=g->seed;
    x^=x<<7;x^=x>>9;x^=x<<8;g->seed=x;return x;
}
void game_new(Game *g,unsigned short seed) {
    unsigned char i;
    for(i=0;i<CELLS;i++)g->cells[i]=0;
    g->seed=seed?seed:0x538e;g->state=READY;g->opened=g->flags=g->placed=0;
}
static unsigned char adjacent(unsigned char a,unsigned char b) {
    signed char x=(signed char)(a%COLS)-(signed char)(b%COLS);
    signed char y=(signed char)(a/COLS)-(signed char)(b/COLS);
    return x>=-1 && x<=1 && y>=-1 && y<=1;
}
static unsigned char nearby(unsigned char p,unsigned char *out) {
    unsigned char x=p%COLS,y=p/COLS,row,col,n=0;
    unsigned char left=x?x-1:0,right=x+1<COLS?x+1:x;
    unsigned char top=y?y-1:0,bottom=y+1<ROWS?y+1:y;
    for(row=top;row<=bottom;row++)for(col=left;col<=right;col++)out[n++]=row*COLS+col;
    return n;
}
static void place(Game *g,unsigned char first) {
    unsigned char p,i,j,n=0,count,around[9];
    while(n<MINES) {
        p=(unsigned char)(random16(g)%CELLS);
        if(!(g->cells[p]&MINE) && !adjacent(p,first)){g->cells[p]|=MINE;n++;}
    }
    for(i=0;i<CELLS;i++)if(!(g->cells[i]&MINE)) {
        n=0;count=nearby(i,around);
        for(j=0;j<count;j++)if(g->cells[around[j]]&MINE)n++;
        g->cells[i]|=n;
    }
    g->placed=1;g->state=PLAYING;
}
static void open_one(Game *g,unsigned char p,unsigned char *tail) {
    if(g->cells[p]&(OPEN|FLAG))return;
    g->cells[p]|=OPEN;
    if(g->cells[p]&MINE){g->state=LOST;return;}
    g->opened++;
    if(!(g->cells[p]&15))g->queue[(*tail)++]=p;
}
void game_open(Game *g,unsigned char p) {
    unsigned char head=0,tail=0,q,i,count,around[9];
    if(p>=CELLS || g->state>=LOST || (g->cells[p]&(FLAG|OPEN)))return;
    if(!g->placed)place(g,p);
    open_one(g,p,&tail);
    while(head<tail && g->state==PLAYING) {
        q=g->queue[head++];
        count=nearby(q,around);
        for(i=0;i<count;i++)open_one(g,around[i],&tail);
    }
    if(g->state==PLAYING && g->opened==CELLS-MINES) {
        g->state=WON;g->flags=MINES;
        for(i=0;i<CELLS;i++)if(g->cells[i]&MINE)g->cells[i]|=FLAG;
    }
}
void game_flag(Game *g,unsigned char p) {
    if(p>=CELLS || g->state>=LOST || (g->cells[p]&OPEN))return;
    g->cells[p]^=FLAG;
    if(g->cells[p]&FLAG)g->flags++;else g->flags--;
}
void game_chord(Game *g,unsigned char p) {
    unsigned char i,n=0,count,around[9];
    if(p>=CELLS || g->state!=PLAYING || !(g->cells[p]&OPEN))return;
    count=nearby(p,around);
    for(i=0;i<count;i++)if(g->cells[around[i]]&FLAG)n++;
    if(n!=(g->cells[p]&15))return;
    for(i=0;i<count && g->state==PLAYING;i++)game_open(g,around[i]);
}
