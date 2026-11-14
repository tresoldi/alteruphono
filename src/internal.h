#ifndef AP_INTERNAL_H
#define AP_INTERNAL_H

#include "alteruphono.h"

#include <stddef.h>
#include <stdint.h>

/* ---- label sets ------------------------------------------------------- */

/* A feature set is a bitset over the context's label table. 256 labels is
 * more than twice what any merkmal system or the 1.x vocabulary needs; a
 * context that would exceed it fails with AP_ERR_LIMIT. */
#define AP_LABEL_WORDS 4
#define AP_MAX_LABELS (AP_LABEL_WORDS * 64)

typedef struct ap_labels {
    uint64_t w[AP_LABEL_WORDS];
} ap_labels;

int api_labels_empty(const ap_labels *a);
int api_labels_equal(const ap_labels *a, const ap_labels *b);
int api_labels_subset(const ap_labels *a, const ap_labels *b);    /* a <= b */
int api_labels_intersect(const ap_labels *a, const ap_labels *b);
int api_labels_has(const ap_labels *a, uint32_t label);
void api_labels_set(ap_labels *a, uint32_t label);
void api_labels_clear(ap_labels *a, uint32_t label);
uint64_t api_labels_hash(const ap_labels *a);

/* ---- string -> id map (open addressing) -------------------------------- */

typedef struct api_strmap {
    char **keys;      /* owned copies */
    uint32_t *values;
    size_t capacity;  /* power of two, 0 when empty */
    size_t count;
} api_strmap;

void api_strmap_free(api_strmap *m);
int api_strmap_get(const api_strmap *m, const char *key, uint32_t *value);
ap_status api_strmap_put(api_strmap *m, const char *key, uint32_t value);
ap_status api_strmap_copy(api_strmap *dst, const api_strmap *src);
uint64_t api_hash_bytes(const void *data, size_t len, uint64_t seed);

/* ---- segments ---------------------------------------------------------- */

typedef struct ap_segment {
    char *grapheme;      /* owned, as given (1.x keeps the atom unnormalized) */
    ap_labels labels;
    int partial;         /* a sound class used as a pattern or element */
    /* 1.x partial_match reads a feature named "-x" as "must not have x";
     * cached here: `positive` is labels minus such names, `negative` the x's */
    ap_labels positive;
    ap_labels negative;
} ap_segment;

typedef struct api_class {
    char *name;
    ap_labels labels;    /* as 1.x stores them: "-x" names included */
} api_class;

/* A universe entry: a grapheme 1.x could look up, with its projected labels
 * computed from merkmal on first use. */
typedef struct api_universe_entry {
    int resolved;
    int found;           /* merkmal resolved it and the projection is non-empty */
    ap_labels labels;
} api_universe_entry;

struct ap_context {
    const mk_system *system;
    ap_context_options options;

    /* labels */
    char **label_names;
    int *label_category;          /* index into category_names, or -1 */
    int *label_negates;           /* for a label "-x", the id of "x"; else -1 */
    size_t label_count;
    api_strmap label_index;
    char **category_names;
    size_t category_count;
    char **alias_from;
    char **alias_to;
    size_t alias_count;
    uint32_t tone_label[5];       /* falling, mid, low, high, rising */
    uint32_t vocabulary_count;    /* labels 0..n-1 are the projection's vocabulary */
    int labial_label;             /* dropped by the projection where a finer place exists */

    /* classes */
    api_class *classes;
    size_t class_count;
    api_strmap class_index;

    /* segments; id 0 is the boundary */
    ap_segment *segs;
    size_t seg_count;
    size_t seg_capacity;
    uint32_t *seg_table;          /* open addressing over seg ids, 0 = empty slot */
    size_t seg_table_capacity;

    /* universe */
    api_strmap universe_index;    /* grapheme -> universe position */
    api_universe_entry *universe;
    size_t universe_count;
    int reverse_built;
    uint32_t *reverse_table;      /* labels -> universe position + 1, first wins */
    size_t reverse_capacity;
};

ap_status api_context_label(ap_context *ctx, const char *name, uint32_t *out);
const char *api_resolve_alias(const ap_context *ctx, const char *name);

/* 1.x grapheme_to_features: exact universe lookup. */
ap_status api_lookup(ap_context *ctx, const char *grapheme, ap_labels *out, int *found);
/* 1.x features_to_grapheme: first universe grapheme with exactly these labels. */
ap_status api_reverse(ap_context *ctx, const ap_labels *labels, const char **out);
/* 1.x features.sound(): class, then exact lookup, then the normalized form. */
ap_status api_make_sound(ap_context *ctx, const char *atom, ap_seg *out);
ap_status api_intern_seg(
    ap_context *ctx, const char *grapheme, const ap_labels *labels, int partial, ap_seg *out);
const ap_segment *api_seg(const ap_context *ctx, ap_seg id);

/* 1.x normalize_output: g -> ɡ, ʼ -> ' ; owned. */
ap_status api_normalize_output(const char *in, char **out);
/* 1.x _normalize_grapheme: NFD plus ɡ->g, ’->ʼ, '->ʼ ; owned. */
ap_status api_normalize_lookup(const char *in, char **out);

/* ---- text -------------------------------------------------------------- */

size_t api_utf8_decode(const unsigned char *s, size_t len, uint32_t *cp);
int api_is_py_space(uint32_t cp);
/* 1.x _preprocess: NFD, Unicode whitespace runs to one space, strip,
 * "->" to ">". Owned. */
ap_status api_preprocess(const char *text, char **out);
/* Splits on single spaces (input is preprocessed); returns owned copies. */
ap_status api_split(const char *text, size_t start, size_t end, char ***parts, size_t *count);
void api_free_parts(char **parts, size_t count);
char *api_strndup(const char *s, size_t n);
char *api_strdup(const char *s);

/* ---- tokens and rules --------------------------------------------------- */

typedef enum api_tok_kind {
    API_TOK_SEGMENT,
    API_TOK_BOUNDARY,
    API_TOK_BACKREF,
    API_TOK_EMPTY,
    API_TOK_CHOICE,
    API_TOK_SET,
    API_TOK_FOCUS,
    API_TOK_QUANT,
    API_TOK_SYLLABLE,
    API_TOK_NEGATION
} api_tok_kind;

typedef enum api_role { API_ROLE_NONE = 0, API_ROLE_ONSET, API_ROLE_NUCLEUS, API_ROLE_CODA } api_role;

typedef struct api_modifier {
    char *text;           /* as written, for 1.x invert_modifiers */
    uint32_t *adds;       /* alias-resolved labels, in written order */
    size_t add_count;
    uint32_t *subs;       /* raw labels */
    size_t sub_count;
} api_modifier;

typedef struct api_tok {
    api_tok_kind kind;
    ap_seg seg;                 /* SEGMENT */
    long index;                 /* BACKREF: 0-based, may be negative (1.x "@0") */
    api_modifier *modifier;     /* BACKREF, or NULL */
    char quantifier;            /* QUANT: '+' or '?' */
    api_role role;              /* SYLLABLE */
    struct api_tok *children;   /* CHOICE, SET: n children; QUANT, NEGATION: 1 */
    size_t child_count;
} api_tok;

struct ap_rule {
    char *source;
    api_tok *ante;
    size_t ante_count;
    api_tok *post;
    size_t post_count;
    size_t left_len;
    size_t right_len;
    int has_quantifiers;        /* at top level of ante, as 1.x checks */
    int has_syllable;
};

void api_tok_free_children(api_tok *tok);
ap_status api_tok_copy(const api_tok *src, api_tok *dst);
ap_status api_modifier_parse(ap_context *ctx, const char *text, api_modifier **out);
void api_modifier_free(api_modifier *m);
/* 1.x apply_modifiers over the context's categories. */
void api_apply_modifier(const ap_context *ctx, const api_modifier *m, const ap_labels *in, ap_labels *out);
/* 1.x invert_modifiers. */
ap_status api_modifier_invert(ap_context *ctx, const api_modifier *m, api_modifier **out);

/* ---- matching ----------------------------------------------------------- */

/* A binding is an element (segment id) or a set index. */
typedef struct api_binding {
    int is_set;
    ap_seg seg;
    size_t set_index;
} api_binding;

/* 1.x _match_one: returns 1 on a match and fills `out`. */
int api_match_one(
    const ap_context *ctx, ap_seg elem, const api_tok *tok,
    const api_role *roles, size_t roles_len, size_t position, api_binding *out);

/* 1.x build_syllable_map over a sequence: roles[i] for every position. */
ap_status api_syllable_roles(
    ap_context *ctx, const ap_seg *seq, size_t n, api_role *roles);

/* Growable segment buffer. */
typedef struct api_segbuf {
    ap_seg *items;
    size_t count;
    size_t capacity;
} api_segbuf;

ap_status api_segbuf_push(api_segbuf *b, ap_seg s);
ap_status api_segbuf_extend(api_segbuf *b, const ap_seg *s, size_t n);
void api_segbuf_free(api_segbuf *b);

/* 1.x match_pattern for backward: matches `pattern` against `seq` (a window
 * of exactly n elements), fixed or variable as 1.x decides from the top-level
 * tokens. Bindings are flat, in sequence order, as 1.x's MatchResult. */
ap_status api_match_pattern(
    const ap_context *ctx, const ap_seg *seq, size_t n,
    const api_tok *pattern, size_t pattern_len,
    int *matched, api_binding **bindings, size_t *binding_count);

/* forward application, and the modifier step it shares with backward */
ap_status api_apply_backref_modifier(
    ap_context *ctx, ap_seg elem, const api_modifier *m, ap_seg *out);

void api_diag(ap_diagnosis *d, ap_status status, size_t offset, const char *fmt, ...);

#endif
