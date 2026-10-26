#include <string.h>
#include "document_counts.h"

/* Leave another mod's page limits alone; restore ours when the Korean mod is deselected. */
static int apply_document_counts(unsigned char *table,int enabled) {
    const unsigned char *wanted=enabled ? document_page_counts : original_document_counts;
    if(!memcmp(table,wanted,16)) return 2;
    if(memcmp(table,enabled ? original_document_counts : document_page_counts,16)) return 0;
    memcpy(table,wanted,16);
    return 1;
}
