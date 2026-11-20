/* Keyboard Minesweeper for the real 7980 application loader. GPL-3.0-or-later. */
#include "game.h"
#include "bbk7980.h"
#include "labels.h"
#include "tiles.h"
Game game;
unsigned char cursor;
static unsigned short entropy;
#define pixel bbk_pixel
#define fill bbk_fill
#define hline bbk_hline
#define tile bbk_tile12
static void label(unsigned char x,unsigned char y,const char *text,unsigned char count,unsigned char shade) {
    (void)count;bbk_text_gbk(x,y,text,12,shade);
}

static const unsigned char digits[10][5]={
 {0x3e,0x51,0x49,0x45,0x3e},{0,0x42,0x7f,0x40,0},
 {0x42,0x61,0x51,0x49,0x46},{0x21,0x41,0x45,0x4b,0x31},
 {0x18,0x14,0x12,0x7f,0x10},{0x27,0x45,0x45,0x45,0x39},
 {0x3c,0x4a,0x49,0x49,0x30},{1,0x71,9,5,3},
 {0x36,0x49,0x49,0x49,0x36},{6,0x49,0x49,0x29,0x1e}};
static void digit(unsigned char x,unsigned char y,unsigned char n,unsigned char shade) {
    unsigned char i,j;
    for(i=0;i<5;i++)for(j=0;j<7;j++)if(digits[n%10][i]&(1<<j))pixel(x+i,y+j,shade);
}
static void number(unsigned char x,unsigned char y,unsigned char n) {
    digit(x,y,n/100,3);digit(x+7,y,(n/10)%10,3);digit(x+14,y,n%10,3);
}
static void draw_cell(unsigned char p) {
    unsigned char x=4+(p%COLS)*12,y=20+(p/COLS)*12,c=game.cells[p],kind;
    if(c&OPEN) {
        kind=(c&MINE)?11:c&15;
    } else {
        kind=9;
        if(game.state==LOST && (c&MINE))kind=11;
        else if(c&FLAG)kind=game.state==LOST?12:10;
    }
    tile(x,y,tile_pixels[kind],p==cursor);
}
static void sidebar(void) {
    fill(152,20,88,100,0);
    label(156,22,label_remaining,2,3);number(202,24,game.flags>MINES?0:MINES-game.flags);
    label(156,42,label_opened,2,3);number(202,44,game.opened);
    hline(156,59,76,1);
    if(game.state==READY)label(160,64,label_ready,4,2);
    else if(game.state==PLAYING)label(160,64,label_playing,3,3);
    else if(game.state==WON)label(160,64,label_won,2,3);
    else label(160,64,label_lost,2,3);
    label(156,82,label_open,2,3);label(192,82,label_enter,3,2);
    label(156,96,label_flag,2,3);label(192,96,label_space,3,2);
    label(156,108,label_new,2,3);label(192,108,label_n,1,2);
}
static void render(void) {
    unsigned char i;
    for(i=0;i<CELLS;i++)draw_cell(i);
    sidebar();
}
static void new_game(void) {
    game_new(&game,entropy+0x538e);cursor=0;
    fill(0,0,240,120,0);fill(0,0,240,17,3);
    label(8,2,label_title,2,0);label(164,2,label_exit,2,0);label(200,2,label_esc,3,0);
    render();
}
static void action(unsigned char key) {
    unsigned char old=cursor;
    if(key==57 && cursor>=COLS)cursor-=COLS;
    else if(key==59 && cursor<CELLS-COLS)cursor+=COLS;
    else if(key==51 && cursor%COLS)cursor--;
    else if(key==58 && cursor%COLS<COLS-1)cursor++;
    else if(key==50){if(game.cells[cursor]&OPEN)game_chord(&game,cursor);else game_open(&game,cursor);render();}
    else if(key==34 || key==44){game_flag(&game,cursor);draw_cell(cursor);sidebar();}
    else if(key==40 || key==45)new_game();
    if(cursor!=old){draw_cell(old);draw_cell(cursor);}
}
int main(void) {
    unsigned char key;
    bbk_event event;
    entropy=(unsigned short)bbk_ticks();new_game();
    while(1) {
        if(!bbk_event_wait(&event) || event.type!=BBK_EVENT_KEY)continue;
        key=(unsigned char)event.value;
        entropy+=(unsigned short)bbk_ticks()+1;
        if(key==BBK_KEY_ESC){bbk_keys_flush();return 0;}
        action(key);
    }
}
