#ifndef MINES_GAME_H
#define MINES_GAME_H
#define COLS 12
#define ROWS 8
#define CELLS (COLS*ROWS)
#define MINES 15
#define MINE 0x80
#define OPEN 0x10
#define FLAG 0x20
#define READY 0
#define PLAYING 1
#define LOST 2
#define WON 3
typedef struct {
    unsigned char cells[CELLS], queue[CELLS];
    unsigned short seed;
    unsigned char state, opened, flags, placed;
} Game;
void game_new(Game *g,unsigned short seed);
void game_open(Game *g,unsigned char position);
void game_flag(Game *g,unsigned char position);
void game_chord(Game *g,unsigned char position);
#endif
