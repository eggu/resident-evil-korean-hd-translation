/* Resident Evil - Korean HD Translation; Classic REbirth 1.1.3 and 1.1.4. */
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "sentence_records.h"
#include "document_pagination.h"
#include "subtitle_position.h"
static uintptr_t rebirth;
#include "rebirth_discover.h"
/* REbirth-relative addresses; 0 = feature absent in that build. */
struct Version {
    const char *name;int legacy;
    uintptr_t sprite,width,mods,reader,movie_update,movie_font;
    uintptr_t sprite_sites[3],width_sites[MAX_WIDTH_SITES],movie_sites[2];unsigned width_count;
};
#define REBIRTH_114_STAMP 0x6ab973bc
/* 1.1.3 (legacy): one selected-mod holder read by thiscall, no HDLoader key and no TrueType
   movie subtitles, so movies stay original and HD tiles are fixed. 1.1.4 and later are discovered. */
static const struct Version rebirth_113={"1.1.3",1,0x1278,0x69440,0x217a8f0,0x46960,0,0,
    {0x68bed,0x68e5c,0x6983c},{0x695d2,0x697a8,0x726b2,0x7285a,0x72d79,0x731c7,0x73378},{0,0},7};
static struct Version discovered={"1.1.4+",0};
static const struct Version *version;
static int (__cdecl *sprite)(void *,int);
static void *checked_mod;
static int mode;
static int performance_checked;
volatile int ko_advance=-1,ko_handled;
static int texture_scale;
static int sd_subtitles;
static void configure_subtitles(void) {
    if(version->legacy) { sd_subtitles=0;return; }
    sd_subtitles=!GetPrivateProfileIntA("DLL","HDLoader",0,".\\config.ini") || GetPrivateProfileIntA("DLL","LowResEnable",0,".\\config.ini");
}
static int __thiscall movie_subtitle_update(void *owner,void *text,int width,int height) {
    unsigned *style=(void *)((unsigned char *)owner+0xc4);
    if((style[0]>>24) && style[2]) style[1]=0;
    return ((int (__thiscall *)(void *,void *,int,int))(rebirth+version->movie_update))(owner,text,width,height);
}
#define SLOT_SIZE 0x21c
#define CACHE_SIZE 128
static unsigned char *const slot=(void *)(0x6977a8+13*SLOT_SIZE);
struct Cached { int id; unsigned age; unsigned char state[SLOT_SIZE]; };
/* shortcut: 128 cached tiles; grow only if a scene exceeds this working set. */
static struct Cached cache[CACHE_SIZE];
static unsigned frame=1,position_reports;
/* Game call targets; replaced by another mod's hook when one already owns the call (we chain to it). */
__attribute__((used)) static uintptr_t next_submit=0x47a9b0,next_choices=0x491830,next_reset=0x47aa20,next_empty=0x491830;
static uintptr_t next_document=0x42bf30;
static int __thiscall reset_draw_commands(void *owner) {
    int result=((int (__thiscall *)(void *))next_reset)(owner);
    frame++;return result;
}
static void log_line(const char *s) {
    FILE *f=fopen("korean_subtitle.log","a");
    if(f) { fprintf(f,"%s\n",s); fclose(f); }
}
#include "movie_subtitle_font.h"
static char *read_mod(const char *path,unsigned *size) {
    uintptr_t begin=*(uintptr_t *)(rebirth+version->mods),end=*(uintptr_t *)(rebirth+version->mods+4);
    if(!begin) return NULL;
    /* 1.1.3: thiscall on the single selected-mod holder; 1.1.4+: stdcall over the mounted-mod vector. */
    if(version->legacy) return ((char *(__thiscall *)(void *,const char *,unsigned *))(rebirth+version->reader))((void *)(rebirth+version->mods),path,size);
    if(begin==end) return NULL;
    return ((char *(__stdcall *)(const char *,unsigned *))(rebirth+version->reader))(path,size);
}
/* REbirth's static CRT allocates from the process heap (no HeapCreate import in 1.1.3/1.1.4). */
static void free_mod(void *data) { if(data) HeapFree(GetProcessHeap(),0,data); }
static int selected(void) {
    if(!performance_checked) {
        performance_checked=1;
        if(GetFileAttributesA("biohazard_performance.dll")!=INVALID_FILE_ATTRIBUTES)
            log_line(LoadLibraryA("biohazard_performance.dll") ? "Existing performance module loaded" : "Performance module load failed");
    }
    void *mod=*(void **)(rebirth+version->mods);
    if(!mod) return 0;
    if(mod!=checked_mod) {
        unsigned size=0; char *data=read_mod("ko_sentence.flag",&size);
        mode=data && size==8 && !memcmp(data,"KOSENT07",8) ? 3 : 0;
        free_mod(data);checked_mod=mod;
        log_line(mode==3 ? "Korean HD Translation renderer enabled" : "Original renderer");
    }
    return mode;
}
static void __cdecl draw_document(void *state) {
    static int reported;
    int result=apply_document_counts((unsigned char *)0x4af1e8,selected()==3);
    if(result==1) log_line("Document page limits updated");
    if(!result && !reported++) log_line("Document page limits unchanged: unexpected table");
    ((void (__cdecl *)(void *))next_document)(state);
}
static void release_slot(void) {
    unsigned count=*(unsigned *)(slot+0x1e0);
    for(unsigned i=0;i<count && i<8;i++) {
        void *texture=*(void **)(slot+0x1e8+i*4);
        if(texture) ((void (__cdecl *)(void *))0x43f2e0)(texture);
    }
    ((void (__thiscall *)(void *))0x498040)(slot);
}
static struct Cached *texture(unsigned id,unsigned tile) {
    unsigned key=id*16+tile+sd_subtitles*SENTENCE_COUNT*16;
    struct Cached *victim=NULL;
    for(unsigned i=0;i<CACHE_SIZE;i++) {
        if(cache[i].id==(int)key) { cache[i].age=frame;return &cache[i]; }
        if(cache[i].id<0) victim=&cache[i];
        else if((!victim || (victim->id>=0 && cache[i].age<victim->age)) && frame-cache[i].age>3) victim=&cache[i];
    }
    if(!victim) { log_line("Sentence cache busy: no safe eviction slot");return NULL; }
    char path[64];snprintf(path,sizeof(path),sd_subtitles ? "sentences-sd/%05u-%02u.tim" : "sentences/%05u-%02u.tim",id,tile);
    unsigned size=0;char *data=read_mod(path,&size);
    if(!data || size!=sentence_records[id][3] || *(uint32_t *)data!=16 || *(uint32_t *)(data+4)!=8) {
        log_line("Sentence texture missing or invalid");free_mod(data);return NULL;
    }
    unsigned char saved[SLOT_SIZE];memcpy(saved,slot,SLOT_SIZE);
    if(victim->id>=0) { memcpy(slot,victim->state,SLOT_SIZE);release_slot(); }
    memset(slot,0,SLOT_SIZE);
    ((void (__thiscall *)(void *))0x4983f0)(slot);
    ((void (__cdecl *)(void *,int,int,int))0x43f700)(data,31,0,1);
    int ok=*(unsigned *)(slot+0x1e0)==1 && *(void **)(slot+0x1e8)!=NULL;
    if(ok) memcpy(victim->state,slot,SLOT_SIZE);
    else release_slot();
    memcpy(slot,saved,SLOT_SIZE);free_mod(data);
    victim->id=ok ? (int)key : -1;victim->age=frame;
    if(ok) { char line[80];snprintf(line,sizeof(line),"Sentence %u loaded (%ux%u)",id,sentence_records[id][0],sentence_records[id][1]);log_line(line); }
    else log_line("Sentence texture upload failed");
    return ok ? victim : NULL;
}
/* Only our tile calls expand source UVs; destination coordinates stay unchanged. */
__attribute__((used)) void __cdecl ko_scale_command(unsigned char *command) {
    if(!texture_scale) return;
    uint16_t *uv=(void *)(command+16);
    uv[0]*=texture_scale;uv[1]*=texture_scale;
    uv[2]=(uv[2]+1)*texture_scale-1;uv[3]=(uv[3]+1)*texture_scale-1;
}
__attribute__((naked)) static void submit_tile(void) {
    __asm__ volatile("pushl %ecx\n pushl 8(%esp)\n call _ko_scale_command\n addl $4,%esp\n popl %ecx\n movl _next_submit,%eax\n jmp *%eax\n");
}
__attribute__((used)) int __cdecl ko_draw(void *descriptor,int light,const unsigned char *raw) {
    unsigned char *d=descriptor;ko_advance=-1;ko_handled=0;
    if(*(uint16_t *)(d+12)!=30 || raw[0]<0xa4 || raw[0]>0xb4 || !selected()) return sprite(descriptor,light);
    ko_advance=0;ko_handled=1;
    if(raw[0]!=0xa4) return 1;
    unsigned id=0;
    for(unsigned i=1;i<=4;i++) { if(raw[i]<0xa5 || raw[i]>0xb4) { log_line("Invalid sentence marker");return 1; } id=id*16+raw[i]-0xa5; }
    if(id>=SENTENCE_COUNT) { log_line("Unknown sentence ID");return 1; }
    unsigned width=sentence_records[id][0],height=sentence_records[id][1],last=sentence_records[id][2];
    unsigned tile_size=256/RENDER_SCALE,cols=(width+tile_size-1)/tile_size,rows=(height+tile_size-1)/tile_size;
    if(!cols || !rows || cols*rows>16) return 1;
    struct Cached *tiles[16];
    for(unsigned i=0;i<cols*rows;i++) { tiles[i]=texture(id,i);if(!tiles[i]) return 1; }
    unsigned char saved[24],saved_slot[SLOT_SIZE];memcpy(saved,d,24);memcpy(saved_slot,slot,SLOT_SIZE);
    int x=*(int16_t *)(d+4),y=*(int16_t *)(d+6);
    int draw_x=sentence_records[id][4] ? 34-*(int16_t *)0x4aa360 : x;
    sentence_position(&draw_x,&y,width,height,*(int16_t *)0x4aa360,*(int16_t *)0x4aa362);
    if(position_reports++<8) {
        char line[160];int ox=*(int16_t *)0x4aa360,oy=*(int16_t *)0x4aa362;
        snprintf(line,sizeof(line),"Korean HD position id=%u origin=%d,%d screen=%d,%d size=%u,%u",id,ox,oy,draw_x+ox,y+oy,width,height);log_line(line);
    }
    int result=1;
    for(unsigned row=0;row<rows;row++) for(unsigned col=0;col<cols;col++) {
        memcpy(slot,tiles[row*cols+col]->state,SLOT_SIZE);
        *(int16_t *)(d+4)=draw_x+col*tile_size;*(int16_t *)(d+6)=y+row*tile_size;
        *(uint16_t *)(d+12)=31;d[14]=0;d[15]=0;
        unsigned w=width-col*tile_size,h=height-row*tile_size;
        *(uint16_t *)(d+8)=w<tile_size ? w : tile_size;
        *(uint16_t *)(d+10)=h<tile_size ? h : tile_size;
        texture_scale=sd_subtitles ? 1 : RENDER_SCALE;result=sprite(descriptor,light);texture_scale=0;
    }
    memcpy(d,saved,24);memcpy(slot,saved_slot,SLOT_SIZE);
    ko_advance=draw_x-x+last;
    /* Carry the last rendered line forward for following dynamic {stringN} fragments. */
    *(int16_t *)(d+6)=y+(int)height-sentence_records[id][5];
    return result;
}
__attribute__((naked)) static void draw_message(void) {
    __asm__ volatile("pushl %esi\n pushl 12(%esp)\n pushl 12(%esp)\n call _ko_draw\n addl $12,%esp\n cmpl $0,_ko_handled\n je 1f\n movl _ko_advance,%ebx\n xorl %edi,%edi\n1: ret\n");
}
__attribute__((naked)) static void draw_insert(void) {
    __asm__ volatile("leal -1(%esi),%eax\n pushl %eax\n pushl 12(%esp)\n pushl 12(%esp)\n call _ko_draw\n addl $12,%esp\n cmpl $0,_ko_handled\n je 1f\n movl _ko_advance,%edi\n xorl %ebx,%ebx\n1: ret\n");
}
static void draw_label(short x,short y,unsigned id) {
    unsigned char d[32]={0};*(unsigned *)d=0x40;
    *(uint16_t *)(d+16)=256;*(uint16_t *)(d+18)=480;
    d[20]=d[21]=d[22]=128;
        unsigned char raw[5]={0xa4,0,0,0,0};
        for(unsigned j=0;j<4;j++) raw[j+1]=0xa5+((id>>(12-j*4))&15);
        /* REbirth 1.1.4 cursors are x=204/244; labels start 12 pixels after each. */
        *(int16_t *)(d+4)=x-*(int16_t *)0x4aa360;
        *(int16_t *)(d+6)=y-*(int16_t *)0x4aa362;
        *(uint16_t *)(d+12)=30;ko_draw(d,2,raw);
}
static void __cdecl draw_choices(short x,short y,unsigned char color,char flags) {
    if(selected()!=3) { ((void (__cdecl *)(short,short,unsigned char,char))next_choices)(x,y,color,flags);return; }
    draw_label(x,y,CHOICE_YES);draw_label(x+40,y,CHOICE_NO);
}
static void __cdecl draw_empty_box(short x,short y,unsigned char color,char flags) {
    if(selected()!=3) { ((void (__cdecl *)(short,short,unsigned char,char))next_empty)(x,y,color,flags);return; }
    if(EMPTY_ITEM!=0xffffffffu) draw_label(x,y,EMPTY_ITEM);
}
__attribute__((used)) int __cdecl ko_text_width(const unsigned char *raw) {
    if(raw[0]==0xa4 && selected()==3) {
        unsigned id=0;
        for(unsigned i=1;i<=4;i++) {
            if(raw[i]<0xa5 || raw[i]>0xb4) return 0;
            id=id*16+raw[i]-0xa5;
        }
        if(id<SENTENCE_COUNT) return sentence_records[id][0];
        return 0;
    }
    return ((int (__thiscall *)(const unsigned char *))(rebirth+version->width))(raw);
}
__attribute__((naked)) static void text_width(void) {
    __asm__ volatile("pushl %ecx\n call _ko_text_width\n addl $4,%esp\n ret\n");
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void *unused) {
    (void)unused;if(reason!=DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(instance);rebirth=(uintptr_t)GetModuleHandleA("ddraw.dll");
    if(!rebirth || (uintptr_t)GetModuleHandleA(NULL)!=0x400000) return TRUE;
    IMAGE_NT_HEADERS32 *nt=(void *)(rebirth+((IMAGE_DOS_HEADER *)rebirth)->e_lfanew);
    if(nt->FileHeader.TimeDateStamp==0x5fcc2a03 && nt->OptionalHeader.SizeOfImage==0x22ce000) version=&rebirth_113;
    else if(nt->FileHeader.TimeDateStamp>=REBIRTH_114_STAMP) {
        struct Discovered d;
        if(!discover_rebirth((const uint8_t *)rebirth,(uint32_t)rebirth,&d)) { log_line("Not installed: REbirth hook points not found");return TRUE; }
        discovered.sprite=d.sprite;discovered.width=d.width;discovered.mods=d.mods;discovered.reader=d.reader;
        discovered.movie_update=d.movie_update;discovered.movie_font=d.movie_font;discovered.width_count=d.width_count;
        memcpy(discovered.sprite_sites,d.sprite_sites,sizeof(d.sprite_sites));
        memcpy(discovered.width_sites,d.width_sites,sizeof(d.width_sites));
        memcpy(discovered.movie_sites,d.movie_sites,sizeof(d.movie_sites));
        if(!d.movie_update) log_line("Movie subtitle hooks not found; movies keep REbirth fonts");
        version=&discovered;
    }
    if(!version) { log_line("Not installed: unsupported REbirth (requires 1.1.3 or later)");return TRUE; }
    IMAGE_NT_HEADERS32 *game_nt=(void *)(0x400000+((IMAGE_DOS_HEADER *)0x400000)->e_lfanew);
    if(game_nt->FileHeader.TimeDateStamp!=0x3642d468 || game_nt->OptionalHeader.SizeOfImage!=0x990000) { log_line("Unsupported game image");return TRUE; }
    uintptr_t target=rebirth+version->sprite;sprite=(void *)target;
    const uintptr_t width_target=rebirth+version->width;
    uintptr_t sites[7+3+MAX_WIDTH_SITES+2]={0x441457,0x491e2b,0x416f96,0x417232,0x4172a8,0x44aa3c,0x42b70f};
    void *targets[7+3+MAX_WIDTH_SITES+2]={submit_tile,draw_choices,reset_draw_commands,reset_draw_commands,reset_draw_commands,draw_empty_box,draw_document};
    uintptr_t expected[7+3+MAX_WIDTH_SITES+2]={0x47a9b0,0x491830,0x47aa20,0x47aa20,0x47aa20,0x491830,0x42bf30};
    unsigned count=7;
    void *const message_targets[3]={draw_insert,draw_message,draw_message};
    for(unsigned i=0;i<3;i++) { sites[count]=rebirth+version->sprite_sites[i];targets[count]=message_targets[i];expected[count++]=target; }
    for(unsigned i=0;i<version->width_count;i++) { sites[count]=rebirth+version->width_sites[i];targets[count]=text_width;expected[count++]=width_target; }
    if(version->movie_update) {
        sites[count]=rebirth+version->movie_sites[0];targets[count]=movie_subtitle_update;expected[count++]=rebirth+version->movie_update;
        sites[count]=rebirth+version->movie_sites[1];targets[count]=movie_font_face;expected[count++]=rebirth+version->movie_font;
    }
    uintptr_t *const next[7]={&next_submit,&next_choices,&next_reset,&next_reset,&next_reset,&next_empty,&next_document};
    for(unsigned i=0;i<count;i++) {
        uintptr_t at=sites[i],actual=*(unsigned char *)at==0xe8 ? at+5+*(int32_t *)(at+1) : 0;
        if(actual && actual==expected[i] && (i>=7 || *next[i]==expected[i])) continue;
        HMODULE owner;char module[MAX_PATH];
        if(i<7 && actual && (*next[i]==expected[i] || *next[i]==actual)
           && GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCSTR)actual,&owner)
           && owner!=GetModuleHandleA(NULL) && GetModuleFileNameA(owner,module,sizeof(module))) {
            char line[MAX_PATH+96];snprintf(line,sizeof(line),"Game call %08lx already hooked by %s; chaining",(unsigned long)at,module);
            log_line(line);*next[i]=actual;continue;
        }
        unsigned char *c=(void *)at;char line[160];
        snprintf(line,sizeof(line),"Unsupported renderer call site %u at %08lx (ddraw+%lx): %02x %02x %02x %02x %02x, expected call %08lx",
            i,(unsigned long)at,(unsigned long)(at-rebirth),c[0],c[1],c[2],c[3],c[4],(unsigned long)expected[i]);
        log_line(line);return TRUE;
    }
    for(unsigned i=0;i<CACHE_SIZE;i++) cache[i].id=-1;
    configure_subtitles();
    log_line(sd_subtitles ? "SD subtitle tiles selected" : "HD subtitle tiles selected");
    for(unsigned i=0;i<count;i++) {
        uintptr_t at=sites[i];DWORD old,ignored;
        if(!VirtualProtect((void *)at,5,PAGE_EXECUTE_READWRITE,&old)) { log_line("Hook protection failure");return TRUE; }
        *(int32_t *)(at+1)=(int32_t)((uintptr_t)targets[i]-at-5);
        FlushInstructionCache(GetCurrentProcess(),(void *)at,5);VirtualProtect((void *)at,5,old,&ignored);
    }
    char line[128];snprintf(line,sizeof(line),"Resident Evil - Korean HD Translation hooks installed (REbirth %s, stamp %08lx)",version->name,(unsigned long)nt->FileHeader.TimeDateStamp);
    log_line(line);return TRUE;
}
