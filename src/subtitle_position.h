/* Game sprite descriptors are relative to the current drawing origin. */
static void sentence_position(int *x,int *y,int width,int height,int origin_x,int origin_y) {
    int screen_x=*x+origin_x,screen_y=*y+origin_y;
    if(screen_x<8 || screen_x+width>312) screen_x=8;
    if(screen_y<4) screen_y=4;
    if(screen_y+height>236) screen_y=236-height;
    *x=screen_x-origin_x;
    *y=screen_y-origin_y;
}
