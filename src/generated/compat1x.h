#ifndef AP_COMPAT1X_H
#define AP_COMPAT1X_H

/* Data of the alteruphono-1 projection; see scripts/gen_compat1x.py. */

#include <stddef.h>

typedef struct ap1_label { const char *name; const char *category; } ap1_label;
typedef struct ap1_alias { const char *from; const char *to; } ap1_alias;
typedef struct ap1_class { const char *name; const char *features; } ap1_class;

extern const ap1_label ap1_vocabulary[];
extern const size_t ap1_vocabulary_count;
extern const ap1_alias ap1_aliases[];
extern const size_t ap1_alias_count;
extern const ap1_class ap1_classes[];
extern const size_t ap1_class_count;
extern const char *const ap1_universe[];
extern const size_t ap1_universe_count;
extern const char ap1_universe_sha256[];

#endif
