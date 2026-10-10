/* REbirth 1.1.4's movie renderer uses FreeType file paths, not font family names. */
static int __cdecl movie_font_face(void *library,const char *original,long index,void **face) {
    int (__cdecl *load)(void *,const char *,long,void **)=(void *)(rebirth+0xf6750);
    const char *name=original;
    for(const char *p=original;*p;p++) if(*p=='\\' || *p=='/') name=p+1;
    if(strcmp(name,"segoeuib.ttf")) return load(library,original,index,face);
    char list[2048],windows[MAX_PATH],path[4096];
    const char *defaults="batang.ttc;fonts\\NotoSerifCJKkr-Regular.otf;segoeuib.ttf;malgun.ttf;segoeui.ttf;arialbd.ttf;arial.ttf";
    DWORD size=GetPrivateProfileStringA("MovieSubtitles","Fonts",defaults,list,sizeof(list),".\\korean_subtitle.ini");
    UINT win_size=GetWindowsDirectoryA(windows,sizeof(windows));
    if(size>=sizeof(list)-1) { log_line("Movie font list too long; using REbirth fallback");return load(library,original,index,face); }
    for(char *next=list;*next;) {
        char *candidate=next;
        while(*next && *next!=';') next++;
        if(*next) *next++=0;
        while(*candidate==' ' || *candidate=='\t') candidate++;
        char *end=candidate+strlen(candidate);
        while(end>candidate && (end[-1]==' ' || end[-1]=='\t')) *--end=0;
        if(!*candidate) continue;
        int has_path=0;
        for(char *p=candidate;*p;p++) if(*p=='\\' || *p=='/' || *p==':') has_path=1;
        if(has_path) snprintf(path,sizeof(path),"%s",candidate);
        else {
            if(!win_size || win_size>=sizeof(windows)) continue;
            snprintf(path,sizeof(path),"%s\\Fonts\\%s",windows,candidate);
        }
        if(!load(library,path,0,face)) {
            FILE *f=fopen("korean_subtitle.log","a");
            if(f) { fprintf(f,"Movie subtitle font: %s\n",path);fclose(f); }
            return 0;
        }
    }
    log_line("Movie fonts unavailable; using REbirth fallback");
    return load(library,original,index,face);
}
