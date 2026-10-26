/* winmm.dll proxy: Classic REbirth imports winmm, so this runs before REbirth's DllMain
   reads its arguments and appends -dev_korean_translation (mod menu skipped, same as manual selection). */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string.h>
#define MOD_FOLDER "mod_korean_translation"
#define AUTO_ARG " -dev_korean_translation"
#define X(name) __attribute__((used)) static FARPROC r_##name;
#include "winmm_exports.h"
#undef X
#define X(name) __attribute__((naked,dllexport)) void name(void) { __asm__ volatile("jmp *_r_" #name); }
#include "winmm_exports.h"
#undef X
static char line[4096];
static LPSTR WINAPI auto_line(void) { return line; }
static void log_line(const char *s) {
    HANDLE f=CreateFileA("korean_subtitle.log",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_ALWAYS,0,NULL);
    if(f==INVALID_HANDLE_VALUE) return;
    DWORD written;WriteFile(f,s,lstrlenA(s),&written,NULL);WriteFile(f,"\r\n",2,&written,NULL);CloseHandle(f);
}
static const char *skip_reason(const char *command) {
    DWORD attributes=GetFileAttributesA(MOD_FOLDER);
    if(attributes==INVALID_FILE_ATTRIBUTES || !(attributes&FILE_ATTRIBUTE_DIRECTORY)) return "Auto-select skipped: " MOD_FOLDER " not found";
    /* Shift or a user-chosen -config/-mod_/-dev_ keeps REbirth's own behaviour, including the mod menu
       (Shift also works on Steam, whose REbirth launcher drops launch options). */
    if(GetAsyncKeyState(VK_SHIFT)&0x8000) return "Auto-select skipped: Shift held";
    if(strstr(command," -config") || strstr(command," -mod_") || strstr(command," -dev_")) return "Auto-select skipped: launch option present";
    if(strlen(command)+sizeof(AUTO_ARG)>sizeof(line)) return "Auto-select skipped: command line too long";
    return NULL;
}
static int patch_rebirth(void) {
    unsigned char *base=(void *)GetModuleHandleA("ddraw.dll");
    if(!base) return 0;
    IMAGE_NT_HEADERS32 *nt=(void *)(base+((IMAGE_DOS_HEADER *)base)->e_lfanew);
    IMAGE_DATA_DIRECTORY dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if(!dir.VirtualAddress) return 0;
    for(IMAGE_IMPORT_DESCRIPTOR *d=(void *)(base+dir.VirtualAddress);d->Name;d++) {
        if(lstrcmpiA((char *)base+d->Name,"KERNEL32.dll") || !d->OriginalFirstThunk) continue;
        IMAGE_THUNK_DATA32 *names=(void *)(base+d->OriginalFirstThunk),*slots=(void *)(base+d->FirstThunk);
        for(;names->u1.AddressOfData;names++,slots++) {
            if(IMAGE_SNAP_BY_ORDINAL32(names->u1.Ordinal)) continue;
            if(strcmp((char *)((IMAGE_IMPORT_BY_NAME *)(base+names->u1.AddressOfData))->Name,"GetCommandLineA")) continue;
            DWORD old,ignored;
            if(!VirtualProtect(&slots->u1.Function,4,PAGE_READWRITE,&old)) return 0;
            slots->u1.Function=(DWORD)(uintptr_t)auto_line;
            VirtualProtect(&slots->u1.Function,4,old,&ignored);
            return 1;
        }
    }
    return 0;
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void *unused) {
    (void)unused;if(reason!=DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(instance);
    char path[MAX_PATH];UINT length=GetSystemDirectoryA(path,MAX_PATH-11);
    if(!length || length>=MAX_PATH-11) return FALSE;
    lstrcatA(path,"\\winmm.dll");
    HMODULE real=LoadLibraryA(path);
    if(!real) return FALSE;
#define X(name) r_##name=GetProcAddress(real,#name);
#include "winmm_exports.h"
#undef X
    const char *command=GetCommandLineA(),*reason_text=skip_reason(command);
    if(reason_text) { log_line(reason_text);return TRUE; }
    lstrcpyA(line,command);lstrcatA(line,AUTO_ARG);
    log_line(patch_rebirth() ? "Auto-select: Korean mod requested from REbirth" : "Auto-select skipped: REbirth ddraw.dll not found");
    return TRUE;
}
