/* Finds REbirth >= 1.1.4 hook points from anchors that survive rebuilds: game-code addresses
   (fixed since 1998), embedded file names and call shapes. Pure C over a mapped image so the
   host test can run it on real ddraw.dll builds. Returns 0 unless every required point is unique. */
#include <stdint.h>
#include <string.h>
#define MAX_WIDTH_SITES 16
struct Discovered {
    uint32_t sprite,width,mods,reader,movie_update,movie_font;
    uint32_t sprite_sites[3],width_sites[MAX_WIDTH_SITES],movie_sites[2];
    unsigned width_count;
};
struct Image { const uint8_t *data;uint32_t size,base,code_start,code_end; };
static uint32_t u32(const struct Image *m,uint32_t at) { uint32_t v;memcpy(&v,m->data+at,4);return v; }
static uint32_t call_target(const struct Image *m,uint32_t at) { return at+5+u32(m,at+1); }
static int is_call_to(const struct Image *m,uint32_t at,uint32_t target) { return m->data[at]==0xe8 && call_target(m,at)==target; }
static int image_open(struct Image *m,const uint8_t *data,uint32_t base) {
    m->data=data;m->base=base;
    uint32_t pe=u32(m,0x3c);
    if(memcmp(data+pe,"PE\0\0",4)) return 0;
    m->size=u32(m,pe+0x50);
    unsigned sections=data[pe+6]|data[pe+7]<<8,optional=data[pe+0x14]|data[pe+0x15]<<8;
    for(unsigned i=0;i<sections;i++) {
        uint32_t s=pe+0x18+optional+i*40;
        if(u32(m,s+36)&0x20) { m->code_start=u32(m,s+12);m->code_end=m->code_start+u32(m,s+8);return m->code_end<=m->size-5; }
    }
    return 0;
}
/* REbirth calls game functions through `jmp [ptr]` thunks whose slot holds the game address. */
static uint32_t find_thunk(const struct Image *m,uint32_t game) {
    uint32_t found=0;
    for(uint32_t at=m->code_start;at<m->code_end && at<m->code_start+0x2000;at++) {
        if(m->data[at]!=0xff || m->data[at+1]!=0x25) continue;
        uint32_t slot=u32(m,at+2)-m->base;
        if(slot<m->size-4 && u32(m,slot)==game) { if(found) return 0;found=at; }
    }
    return found;
}
static int contains(const uint8_t *hay,size_t hay_size,const char *needle,size_t size) {
    for(size_t i=0;i+size<=hay_size;i++) if(!memcmp(hay+i,needle,size)) return 1;
    return 0;
}
/* Sprite callers that draw message text, told apart by the game globals they touch. */
static int classify_sprite_site(const struct Image *m,uint32_t at) {
    const uint8_t *before=m->data+at-48;
    if(!memcmp(m->data+at-3,"\x66\x29\x18",3)) return 0;                      /* sub [0xc30034],bx: inserted text */
    if(contains(before,48,"\x80\x3d\xf1\x86\xc3\x00\x11",7)) return 1;          /* cmp [0xc386f1],0x11: message */
    if(contains(before,48,"\xa2\x3e\x00\xc3\x00",5)) return 2;                  /* mov [0xc3003e],al: message */
    return -1;
}
/* mask: 'x' = byte must match, '?' = relocated or rel32 operand. */
static uint32_t find_signature(const struct Image *m,const char *bytes,const char *mask,unsigned call_offset) {
    unsigned size=strlen(mask);uint32_t found=0;
    for(uint32_t at=m->code_start;at+size<=m->code_end;at++) {
        unsigned i=0;
        while(i<size && (mask[i]=='?' || m->data[at+i]==(uint8_t)bytes[i])) i++;
        if(i<size) continue;
        if(found) return 0;
        found=at+call_offset;
    }
    return found && m->data[found]==0xe8 ? found : 0;
}
static int discover_rebirth(const uint8_t *data,uint32_t base,struct Discovered *d) {
    struct Image m;memset(d,0,sizeof(*d));
    if(!image_open(&m,data,base)) return 0;
    d->sprite=find_thunk(&m,0x441120);
    uint32_t name_thunk=find_thunk(&m,0x491440);
    if(!d->sprite || !name_thunk) return 0;
    for(uint32_t at=m.code_start+48;at<m.code_end;at++) {
        if(is_call_to(&m,at,d->sprite)) {
            int kind=classify_sprite_site(&m,at);
            if(kind>=0) { if(d->sprite_sites[kind]) return 0;d->sprite_sites[kind]=at; }
        }
        /* call <name thunk>; mov ecx,eax; call width */
        if(is_call_to(&m,at,name_thunk) && !memcmp(m.data+at+5,"\x8b\xc8\xe8",3)) {
            uint32_t width=call_target(&m,at+7);
            if(d->width && d->width!=width) return 0;
            d->width=width;
        }
    }
    if(!d->sprite_sites[0] || !d->sprite_sites[1] || !d->sprite_sites[2] || !d->width) return 0;
    for(uint32_t at=m.code_start;at<m.code_end;at++)
        if(is_call_to(&m,at,d->width)) { if(d->width_count==MAX_WIDTH_SITES) return 0;d->width_sites[d->width_count++]=at; }
    /* push "encoding.xml"; call reader(path,&size) — stdcall, then mov esi,[mods]; push edi; mov edi,[mods+4] */
    uint32_t name=0;
    for(uint32_t at=0x1000;at+13<=m.size && !name;at++) if(!memcmp(data+at,"encoding.xml",13)) name=at;
    for(uint32_t at=m.code_start;name && at<m.code_end && !d->reader;at++) {
        if(data[at]!=0x68 || u32(&m,at+1)!=base+name) continue;
        for(uint32_t call=at+5;call<at+24;call++) if(data[call]==0xe8) {
            if(!memcmp(data+call+5,"\x83\xc4\x08",3)) return 0;
            d->reader=call_target(&m,call);break;
        }
    }
    if(!d->reader || d->reader>=m.code_end) return 0;
    for(uint32_t at=d->reader;at<d->reader+0x40 && !d->mods;at++)
        if(!memcmp(data+at,"\x8b\x35",2) && !memcmp(data+at+6,"\x57\x8b\x3d",3) && u32(&m,at+9)==u32(&m,at+2)+4) d->mods=u32(&m,at+2)-base;
    if(!d->mods || d->mods>=m.size) return 0;
    /* Movie subtitle style and font calls (optional: without them movies keep REbirth's look). */
    d->movie_sites[0]=find_signature(&m,"\xff\x75\xec\xb9\0\0\0\0\xff\x75\xe8\x50\xe8\0\0\0\0\xb9\0\0\0\0","xxxx????xxxxx????x????",12);
    d->movie_sites[1]=find_signature(&m,"\x8d\x71\x3c\x56\x6a\0\x50\xff\x71\x38\xe8\0\0\0\0\x8b\x4d\xdc","xxxxxxxxxxx????xxx",10);
    if(d->movie_sites[0] && d->movie_sites[1]) {
        d->movie_update=call_target(&m,d->movie_sites[0]);d->movie_font=call_target(&m,d->movie_sites[1]);
    } else d->movie_sites[0]=d->movie_sites[1]=0;
    return 1;
}
