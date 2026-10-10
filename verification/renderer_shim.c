__declspec(dllexport) int __cdecl ko_draw(void *,int,const unsigned char *);
__declspec(dllexport) extern volatile int ko_advance;
#include <stddef.h>
__attribute__((noinline,optnone)) __declspec(dllexport) int verify_snprintf(char *,size_t,const char *,...);
#define snprintf verify_snprintf
#include "../src/korean_subtitle.c"
__attribute__((noinline,optnone)) __declspec(dllexport) int verify_snprintf(char *dst,size_t count,const char *format,...) { return -1; }
__declspec(dllexport) void verify_init(unsigned base, int m) {
 rebirth=base;sprite=(void *)(base+0x128c);mode=m;performance_checked=1;
 checked_mod=*(void **)(base+0x229e290);
 *(int *)(0x441457+1)=(int)((unsigned)submit_tile-0x441457-5);
 *(int *)(0x491e2b+1)=(int)((unsigned)draw_choices-0x491e2b-5);
 const unsigned widths[]={0x61d22,0x61efb,0x6e902,0x6eaaa,0x6efcb,0x6f3a7,0x6f518};
 for(unsigned i=0;i<7;i++) *(int *)(base+widths[i]+1)=(int)((unsigned)text_width-base-widths[i]-5);
 *(int *)(base+0x61f8f+1)=(int)((unsigned)draw_message-base-0x61f8f-5);
 const unsigned resets[]={0x416f96,0x417232,0x4172a8};
 for(unsigned i=0;i<3;i++) *(int *)(resets[i]+1)=(int)((unsigned)reset_draw_commands-resets[i]-5);
 for(unsigned i=0;i<CACHE_SIZE;i++)cache[i].id=-1;
}
__declspec(dllexport) void *verify_message(void) {return draw_message;}
__declspec(dllexport) void *verify_insert(void) {return draw_insert;}

__declspec(dllexport) void verify_choices(short x,short y) {draw_choices(x,y,0,0);}
__declspec(dllexport) char *verify_read_file(const char *path,unsigned *size) { return read_mod(path,size); }

__declspec(dllexport) void verify_fill_cache(void) {
 for(unsigned i=0;i<CACHE_SIZE;i++) {cache[i].id=60000+i;cache[i].age=frame;memset(cache[i].state,0,SLOT_SIZE);}
}
__declspec(dllexport) unsigned verify_cache_frame(void) {return frame;}
__declspec(dllexport) void verify_subtitle_mode(int sd) {sd_subtitles=sd;}
__declspec(dllexport) int verify_configure_subtitles(void) {configure_subtitles();return sd_subtitles;}
__declspec(dllexport) void *verify_movie_update(void) {return movie_subtitle_update;}
__declspec(dllexport) void *verify_empty_box(void) {return draw_empty_box;}
__declspec(dllexport) void *verify_movie_font(void) {return movie_font_face;}
