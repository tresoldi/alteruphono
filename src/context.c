#include "internal.h"

#include "generated/compat1x.h"

#include <stdlib.h>
#include <string.h>

/* ---- options ------------------------------------------------------------ */

void ap_context_options_init_defaults(ap_context_options *options)
{
    if (options == NULL) {
        return;
    }
    options->projection = AP_PROJECTION_ALTERUPHONO_1;
    options->max_backward_candidates = 100000;
}

/* ---- labels ------------------------------------------------------------- */

static ap_status add_category(ap_context *ctx, const char *name, int *out)
{
    size_t i;
    char **grown;

    for (i = 0; i < ctx->category_count; i++) {
        if (strcmp(ctx->category_names[i], name) == 0) {
            *out = (int)i;
            return AP_OK;
        }
    }
    grown = (char **)realloc(ctx->category_names, (ctx->category_count + 1) * sizeof(char *));
    if (grown == NULL) {
        return AP_ERR_OOM;
    }
    ctx->category_names = grown;
    ctx->category_names[ctx->category_count] = api_strdup(name);
    if (ctx->category_names[ctx->category_count] == NULL) {
        return AP_ERR_OOM;
    }
    *out = (int)ctx->category_count++;
    return AP_OK;
}

static ap_status add_label(ap_context *ctx, const char *name, int category, uint32_t *out)
{
    uint32_t id;
    uint32_t target = 0;
    int negates = -1;
    char **names;
    int *cats;
    int *negs;

    if (api_strmap_get(&ctx->label_index, name, &id)) {
        *out = id;
        return AP_OK;
    }
    if (name[0] == '-') {
        ap_status st = add_label(ctx, name + 1, -1, &target);
        if (st != AP_OK) {
            return st;
        }
        negates = (int)target;
    }
    if (ctx->label_count >= AP_MAX_LABELS) {
        return AP_ERR_LIMIT;
    }
    names = (char **)realloc(ctx->label_names, (ctx->label_count + 1) * sizeof(char *));
    if (names == NULL) {
        return AP_ERR_OOM;
    }
    ctx->label_names = names;
    cats = (int *)realloc(ctx->label_category, (ctx->label_count + 1) * sizeof(int));
    if (cats == NULL) {
        return AP_ERR_OOM;
    }
    ctx->label_category = cats;
    negs = (int *)realloc(ctx->label_negates, (ctx->label_count + 1) * sizeof(int));
    if (negs == NULL) {
        return AP_ERR_OOM;
    }
    ctx->label_negates = negs;
    ctx->label_negates[ctx->label_count] = negates;
    ctx->label_names[ctx->label_count] = api_strdup(name);
    if (ctx->label_names[ctx->label_count] == NULL) {
        return AP_ERR_OOM;
    }
    ctx->label_category[ctx->label_count] = category;
    id = (uint32_t)ctx->label_count;
    if (api_strmap_put(&ctx->label_index, name, id) != AP_OK) {
        free(ctx->label_names[ctx->label_count]);
        return AP_ERR_OOM;
    }
    ctx->label_count++;
    *out = id;
    return AP_OK;
}

ap_status api_context_label(ap_context *ctx, const char *name, uint32_t *out)
{
    return add_label(ctx, name, -1, out);
}

const char *api_resolve_alias(const ap_context *ctx, const char *name)
{
    size_t i;

    for (i = 0; i < ctx->alias_count; i++) {
        if (strcmp(ctx->alias_from[i], name) == 0) {
            return ctx->alias_to[i];
        }
    }
    return name;
}

/* ---- segments ----------------------------------------------------------- */

static uint64_t seg_hash(const char *grapheme, const ap_labels *labels, int partial)
{
    uint64_t h = api_hash_bytes(grapheme, strlen(grapheme), (uint64_t)partial);
    return h ^ (api_labels_hash(labels) * 31u);
}

const ap_segment *api_seg(const ap_context *ctx, ap_seg id)
{
    return &ctx->segs[id];
}

static ap_status seg_table_grow(ap_context *ctx)
{
    size_t cap = ctx->seg_table_capacity == 0 ? 64 : ctx->seg_table_capacity * 2;
    uint32_t *table = (uint32_t *)calloc(cap, sizeof(uint32_t));
    size_t id;

    if (table == NULL) {
        return AP_ERR_OOM;
    }
    for (id = 1; id < ctx->seg_count; id++) {
        const ap_segment *s = &ctx->segs[id];
        size_t i = (size_t)seg_hash(s->grapheme, &s->labels, s->partial) & (cap - 1);
        while (table[i] != 0) {
            i = (i + 1) & (cap - 1);
        }
        table[i] = (uint32_t)id;
    }
    free(ctx->seg_table);
    ctx->seg_table = table;
    ctx->seg_table_capacity = cap;
    return AP_OK;
}

ap_status api_intern_seg(
    ap_context *ctx, const char *grapheme, const ap_labels *labels, int partial, ap_seg *out)
{
    size_t i;
    size_t mask;

    if ((ctx->seg_count + 1) * 2 > ctx->seg_table_capacity) {
        ap_status st = seg_table_grow(ctx);
        if (st != AP_OK) {
            return st;
        }
    }
    mask = ctx->seg_table_capacity - 1;
    i = (size_t)seg_hash(grapheme, labels, partial) & mask;
    while (ctx->seg_table[i] != 0) {
        const ap_segment *s = &ctx->segs[ctx->seg_table[i]];
        if (s->partial == partial && api_labels_equal(&s->labels, labels)
            && strcmp(s->grapheme, grapheme) == 0) {
            *out = ctx->seg_table[i];
            return AP_OK;
        }
        i = (i + 1) & mask;
    }
    if (ctx->seg_count >= UINT32_MAX - 1) {
        return AP_ERR_LIMIT;
    }
    if (ctx->seg_count == ctx->seg_capacity) {
        size_t cap = ctx->seg_capacity * 2;
        ap_segment *grown = (ap_segment *)realloc(ctx->segs, cap * sizeof(ap_segment));
        if (grown == NULL) {
            return AP_ERR_OOM;
        }
        ctx->segs = grown;
        ctx->seg_capacity = cap;
    }
    ctx->segs[ctx->seg_count].grapheme = api_strdup(grapheme);
    if (ctx->segs[ctx->seg_count].grapheme == NULL) {
        return AP_ERR_OOM;
    }
    ctx->segs[ctx->seg_count].labels = *labels;
    ctx->segs[ctx->seg_count].partial = partial;
    {
        ap_segment *s = &ctx->segs[ctx->seg_count];
        size_t j;
        s->positive = *labels;
        memset(&s->negative, 0, sizeof(s->negative));
        for (j = 0; j < ctx->label_count; j++) {
            if (ctx->label_negates[j] >= 0 && api_labels_has(labels, (uint32_t)j)) {
                api_labels_clear(&s->positive, (uint32_t)j);
                api_labels_set(&s->negative, (uint32_t)ctx->label_negates[j]);
            }
        }
    }
    ctx->seg_table[i] = (uint32_t)ctx->seg_count;
    *out = (ap_seg)ctx->seg_count++;
    return AP_OK;
}

/* ---- the projection ----------------------------------------------------- */

static int tone_digit(const char *label, const char *prefix)
{
    size_t n = strlen(prefix);

    if (strncmp(label, prefix, n) == 0 && label[n] >= '0' && label[n] <= '9' && label[n + 1] == '\0') {
        return label[n] - '0';
    }
    return -1;
}

/* merkmal labels -> alteruphono-1 labels (docs/v2/DESIGN.md section 4.1):
 * keep the 1.x vocabulary, drop merkmal's hierarchical `labial` where a finer
 * place is present, and map
 * merkmal's tone contour (onset, mid, offset) to 1.x's five tone names. */
static ap_status project(ap_context *ctx, const char *grapheme, ap_labels *out, int *found)
{
    mk_string_list *list = NULL;
    mk_status ms;
    size_t i;
    size_t n;
    int onset = -1;
    int mid = -1;
    int offset = -1;
    int tone = 0;

    memset(out, 0, sizeof(*out));
    *found = 0;
    ms = mk_system_grapheme_features(ctx->system, grapheme, &list);
    if (ms == MK_ERR_OOM) {
        return AP_ERR_OOM;
    }
    if (ms != MK_OK) {
        return AP_OK; /* merkmal does not know it: 1.x's None */
    }
    n = mk_string_list_size(list);
    for (i = 0; i < n; i++) {
        const char *label = mk_string_list_get(list, i);
        uint32_t id;
        int d;

        if ((d = tone_digit(label, "tone-onset-")) >= 0) {
            onset = d;
        } else if ((d = tone_digit(label, "tone-mid-")) >= 0) {
            mid = d;
        } else if ((d = tone_digit(label, "tone-offset-")) >= 0) {
            offset = d;
        } else if (strcmp(label, "tone-present") == 0) {
            tone = 1;
        } else if (api_strmap_get(&ctx->label_index, label, &id) && id < ctx->vocabulary_count) {
            api_labels_set(out, id);
        }
    }
    mk_string_list_free(list);
    /* merkmal's `labial` is a major-place label above bilabial/labio-dental;
     * 1.x uses it only as the place of segments with no finer place (ʘ).
     * Keep it only when it is the sole place label. */
    if (ctx->labial_label >= 0 && api_labels_has(out, (uint32_t)ctx->labial_label)) {
        int place = ctx->label_category[ctx->labial_label];
        uint32_t j;
        for (j = 0; j < ctx->vocabulary_count; j++) {
            if ((int)j != ctx->labial_label && ctx->label_category[j] == place && api_labels_has(out, j)) {
                api_labels_clear(out, (uint32_t)ctx->labial_label);
                break;
            }
        }
    }
    if (tone) {
        int t = -1;
        if (onset == 4 && mid == 3 && offset == 2) {
            t = 0; /* falling */
        } else if (onset == 3 && mid == 3 && offset == 3) {
            t = 1; /* mid */
        } else if (onset == 2 && mid == 2 && offset == 2) {
            t = 2; /* low */
        } else if (onset == 4 && mid == 4 && offset == 4) {
            t = 3; /* high */
        } else if (onset == 2 && mid == 3 && offset == 4) {
            t = 4; /* rising */
        }
        if (t >= 0) {
            api_labels_set(out, ctx->tone_label[t]);
        }
    }
    *found = !api_labels_empty(out);
    return AP_OK;
}

ap_status api_lookup(ap_context *ctx, const char *grapheme, ap_labels *out, int *found)
{
    uint32_t pos;
    api_universe_entry *e;

    memset(out, 0, sizeof(*out));
    *found = 0;
    if (!api_strmap_get(&ctx->universe_index, grapheme, &pos)) {
        return AP_OK;
    }
    e = &ctx->universe[pos];
    if (!e->resolved) {
        ap_status st = project(ctx, grapheme, &e->labels, &e->found);
        if (st != AP_OK) {
            return st;
        }
        e->resolved = 1;
    }
    *out = e->labels;
    *found = e->found;
    return AP_OK;
}

static ap_status build_reverse(ap_context *ctx)
{
    size_t cap = 16;
    size_t i;

    while (cap < ctx->universe_count * 2) {
        cap *= 2;
    }
    ctx->reverse_table = (uint32_t *)calloc(cap, sizeof(uint32_t));
    if (ctx->reverse_table == NULL) {
        return AP_ERR_OOM;
    }
    ctx->reverse_capacity = cap;
    for (i = 0; i < ctx->universe_count; i++) {
        ap_labels labels;
        int found;
        size_t slot;
        ap_status st = api_lookup(ctx, ap1_universe[i], &labels, &found);

        if (st != AP_OK) {
            return st;
        }
        if (!found) {
            continue;
        }
        slot = (size_t)api_labels_hash(&labels) & (cap - 1);
        while (ctx->reverse_table[slot] != 0) {
            const api_universe_entry *other = &ctx->universe[ctx->reverse_table[slot] - 1];
            if (api_labels_equal(&other->labels, &labels)) {
                break; /* first in file order wins */
            }
            slot = (slot + 1) & (cap - 1);
        }
        if (ctx->reverse_table[slot] == 0) {
            ctx->reverse_table[slot] = (uint32_t)(i + 1);
        }
    }
    ctx->reverse_built = 1;
    return AP_OK;
}

ap_status api_reverse(ap_context *ctx, const ap_labels *labels, const char **out)
{
    size_t slot;

    *out = NULL;
    if (!ctx->reverse_built) {
        ap_status st = build_reverse(ctx);
        if (st != AP_OK) {
            return st;
        }
    }
    slot = (size_t)api_labels_hash(labels) & (ctx->reverse_capacity - 1);
    while (ctx->reverse_table[slot] != 0) {
        uint32_t pos = ctx->reverse_table[slot] - 1;
        if (api_labels_equal(&ctx->universe[pos].labels, labels)) {
            *out = ap1_universe[pos];
            return AP_OK;
        }
        slot = (slot + 1) & (ctx->reverse_capacity - 1);
    }
    return AP_OK;
}

/* ---- normalizations of 1.x ---------------------------------------------- */

static ap_status map_chars(const char *in, int to_output, char **out)
{
    /* g (U+0067) <-> ɡ (U+0261); ʼ (U+02BC) <- ’ (U+2019) and ' */
    size_t len = strlen(in);
    char *buf = (char *)malloc(len * 3 + 1);
    size_t i = 0;
    size_t w = 0;

    if (buf == NULL) {
        return AP_ERR_OOM;
    }
    while (i < len) {
        const unsigned char *p = (const unsigned char *)in + i;
        if (to_output) {
            if (p[0] == 'g') {
                memcpy(buf + w, "\xc9\xa1", 2);
                w += 2;
                i += 1;
                continue;
            }
            if (len - i >= 2 && p[0] == 0xCA && p[1] == 0xBC) {
                buf[w++] = '\'';
                i += 2;
                continue;
            }
        } else {
            if (len - i >= 2 && p[0] == 0xC9 && p[1] == 0xA1) {
                buf[w++] = 'g';
                i += 2;
                continue;
            }
            if (len - i >= 3 && p[0] == 0xE2 && p[1] == 0x80 && p[2] == 0x99) {
                memcpy(buf + w, "\xca\xbc", 2);
                w += 2;
                i += 3;
                continue;
            }
            if (p[0] == '\'') {
                memcpy(buf + w, "\xca\xbc", 2);
                w += 2;
                i += 1;
                continue;
            }
        }
        buf[w++] = in[i++];
    }
    buf[w] = '\0';
    *out = buf;
    return AP_OK;
}

ap_status api_normalize_output(const char *in, char **out)
{
    return map_chars(in, 1, out);
}

ap_status api_normalize_lookup(const char *in, char **out)
{
    char *nfd = NULL;
    mk_status ms = mk_unicode_normalize(in, MK_NFD, &nfd);
    ap_status st;

    *out = NULL;
    if (ms != MK_OK) {
        return ms == MK_ERR_OOM ? AP_ERR_OOM : AP_ERR_MERKMAL;
    }
    st = map_chars(nfd, 0, out);
    mk_string_free(nfd);
    return st;
}

ap_status api_make_sound(ap_context *ctx, const char *atom, ap_seg *out)
{
    uint32_t cls;
    ap_labels labels;
    int found;
    ap_status st;

    if (api_strmap_get(&ctx->class_index, atom, &cls)) {
        return api_intern_seg(ctx, atom, &ctx->classes[cls].labels, 1, out);
    }
    st = api_lookup(ctx, atom, &labels, &found);
    if (st != AP_OK) {
        return st;
    }
    if (!found) {
        char *norm = NULL;
        st = api_normalize_lookup(atom, &norm);
        if (st != AP_OK) {
            return st;
        }
        if (strcmp(norm, atom) != 0) {
            st = api_lookup(ctx, norm, &labels, &found);
        }
        free(norm);
        if (st != AP_OK) {
            return st;
        }
    }
    if (!found) {
        memset(&labels, 0, sizeof(labels));
    }
    return api_intern_seg(ctx, atom, &labels, 0, out);
}

/* ---- modifiers ---------------------------------------------------------- */

void api_modifier_free(api_modifier *m)
{
    if (m == NULL) {
        return;
    }
    free(m->text);
    free(m->adds);
    free(m->subs);
    free(m);
}

static int is_strip_space(char c)
{
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v';
}

ap_status api_modifier_parse(ap_context *ctx, const char *text, api_modifier **out)
{
    api_modifier *m = (api_modifier *)calloc(1, sizeof(api_modifier));
    size_t len = strlen(text);
    size_t start = 0;
    ap_status st = AP_OK;

    *out = NULL;
    if (m == NULL) {
        return AP_ERR_OOM;
    }
    m->text = api_strdup(text);
    m->adds = (uint32_t *)malloc((len + 1) * sizeof(uint32_t));
    m->subs = (uint32_t *)malloc((len + 1) * sizeof(uint32_t));
    if (m->text == NULL || m->adds == NULL || m->subs == NULL) {
        api_modifier_free(m);
        return AP_ERR_OOM;
    }
    /* 1.x: split on ",", strip, "+x" adds, "-x" subtracts, bare "x" adds.
     * Text is preprocessed, so the only whitespace left is ' '. */
    while (st == AP_OK && start <= len) {
        size_t end = start;
        size_t a;
        size_t b;
        char *item;
        uint32_t id;

        while (end < len && text[end] != ',') {
            end++;
        }
        a = start;
        b = end;
        while (a < b && is_strip_space(text[a])) {
            a++;
        }
        while (b > a && is_strip_space(text[b - 1])) {
            b--;
        }
        if (a < b && (text[a] == '+' || text[a] == '-')) {
            int add = text[a] == '+';
            item = api_strndup(text + a + 1, b - a - 1);
            if (item == NULL) {
                st = AP_ERR_OOM;
                break;
            }
            if (add) {
                st = api_context_label(ctx, api_resolve_alias(ctx, item), &id);
                if (st == AP_OK) {
                    m->adds[m->add_count++] = id;
                }
            } else {
                st = api_context_label(ctx, item, &id);
                if (st == AP_OK) {
                    m->subs[m->sub_count++] = id;
                }
            }
        } else {
            item = api_strndup(text + a, b - a);
            if (item == NULL) {
                st = AP_ERR_OOM;
                break;
            }
            st = api_context_label(ctx, api_resolve_alias(ctx, item), &id);
            if (st == AP_OK) {
                m->adds[m->add_count++] = id;
            }
        }
        free(item);
        start = end + 1;
    }
    if (st != AP_OK) {
        api_modifier_free(m);
        return st;
    }
    *out = m;
    return AP_OK;
}

void api_apply_modifier(const ap_context *ctx, const api_modifier *m, const ap_labels *in, ap_labels *out)
{
    /* 1.x add_features: each addition removes every label of its category,
     * then is added; subtractions are removed afterwards. 1.x iterates a
     * frozenset, so two additions in one category resolve in hash order;
     * here they resolve in written order (the last wins). */
    size_t i;
    size_t j;

    *out = *in;
    for (i = 0; i < m->add_count; i++) {
        uint32_t add = m->adds[i];
        int cat = ctx->label_category[add];
        if (cat >= 0) {
            for (j = 0; j < ctx->label_count; j++) {
                if (ctx->label_category[j] == cat) {
                    api_labels_clear(out, (uint32_t)j);
                }
            }
        }
        api_labels_set(out, add);
    }
    for (i = 0; i < m->sub_count; i++) {
        api_labels_clear(out, m->subs[i]);
    }
}

ap_status api_modifier_invert(ap_context *ctx, const api_modifier *m, api_modifier **out)
{
    /* 1.x invert_modifiers works on the text: "+x" -> "-x", "-x" -> "+x",
     * bare "x" -> "-x"; then the result is parsed again (so "+plosive"
     * inverted is "-plosive", a raw subtraction, not "-stop"). */
    size_t len = strlen(m->text);
    char *buf = (char *)malloc(len * 2 + 2);
    size_t start = 0;
    size_t w = 0;
    ap_status st;

    *out = NULL;
    if (buf == NULL) {
        return AP_ERR_OOM;
    }
    while (start <= len) {
        size_t end = start;
        size_t a;
        size_t b;
        while (end < len && m->text[end] != ',') {
            end++;
        }
        a = start;
        b = end;
        while (a < b && is_strip_space(m->text[a])) {
            a++;
        }
        while (b > a && is_strip_space(m->text[b - 1])) {
            b--;
        }
        if (w > 0) {
            buf[w++] = ',';
        }
        if (a < b && m->text[a] == '+') {
            buf[w++] = '-';
            a++;
        } else if (a < b && m->text[a] == '-') {
            buf[w++] = '+';
            a++;
        } else {
            buf[w++] = '-';
        }
        memcpy(buf + w, m->text + a, b - a);
        w += b - a;
        start = end + 1;
    }
    buf[w] = '\0';
    st = api_modifier_parse(ctx, buf, out);
    free(buf);
    return st;
}

ap_status api_apply_backref_modifier(ap_context *ctx, ap_seg elem, const api_modifier *m, ap_seg *out)
{
    /* 1.x forward: a modifier applies to a Sound with features; the result's
     * grapheme is features_to_grapheme (normalized for output) or, failing
     * that, the old grapheme, and its features are the new set either way. */
    const ap_segment *s;
    ap_labels labels;
    const char *g = NULL;
    char *norm = NULL;
    ap_status st;

    *out = elem;
    if (elem == AP_SEG_BOUNDARY) {
        return AP_OK;
    }
    s = api_seg(ctx, elem);
    if (api_labels_empty(&s->labels)) {
        return AP_OK;
    }
    api_apply_modifier(ctx, m, &s->labels, &labels);
    st = api_reverse(ctx, &labels, &g);
    if (st != AP_OK) {
        return st;
    }
    if (g != NULL) {
        st = api_normalize_output(g, &norm);
        if (st != AP_OK) {
            return st;
        }
        st = api_intern_seg(ctx, norm, &labels, 0, out);
        free(norm);
        return st;
    }
    {
        char *old = api_strdup(api_seg(ctx, elem)->grapheme);
        if (old == NULL) {
            return AP_ERR_OOM;
        }
        st = api_intern_seg(ctx, old, &labels, 0, out);
        free(old);
    }
    return st;
}

/* ---- context lifecycle -------------------------------------------------- */

static ap_status context_init(ap_context *ctx)
{
    size_t i;
    ap_status st;
    static const char *const tones[5] = {
        "with_falling_tone", "with_mid_tone", "with_low_tone", "with_high_tone", "with_rising_tone"
    };

    for (i = 0; i < ap1_vocabulary_count; i++) {
        int cat = -1;
        uint32_t id;
        if (ap1_vocabulary[i].category != NULL) {
            st = add_category(ctx, ap1_vocabulary[i].category, &cat);
            if (st != AP_OK) {
                return st;
            }
        }
        st = add_label(ctx, ap1_vocabulary[i].name, cat, &id);
        if (st != AP_OK) {
            return st;
        }
    }
    ctx->vocabulary_count = (uint32_t)ctx->label_count;
    {
        uint32_t id;
        ctx->labial_label = api_strmap_get(&ctx->label_index, "labial", &id) ? (int)id : -1;
        for (i = 0; i < 5; i++) {
            if (!api_strmap_get(&ctx->label_index, tones[i], &ctx->tone_label[i])) {
                return AP_ERR_INVALID_ARGUMENT;
            }
        }
    }
    ctx->alias_from = (char **)calloc(ap1_alias_count + 1, sizeof(char *));
    ctx->alias_to = (char **)calloc(ap1_alias_count + 1, sizeof(char *));
    if (ctx->alias_from == NULL || ctx->alias_to == NULL) {
        return AP_ERR_OOM;
    }
    for (i = 0; i < ap1_alias_count; i++) {
        ctx->alias_from[i] = api_strdup(ap1_aliases[i].from);
        ctx->alias_to[i] = api_strdup(ap1_aliases[i].to);
        if (ctx->alias_from[i] == NULL || ctx->alias_to[i] == NULL) {
            return AP_ERR_OOM;
        }
        ctx->alias_count++;
    }
    ctx->classes = (api_class *)calloc(ap1_class_count + 1, sizeof(api_class));
    if (ctx->classes == NULL) {
        return AP_ERR_OOM;
    }
    for (i = 0; i < ap1_class_count; i++) {
        api_class *c = &ctx->classes[i];
        const char *f = ap1_classes[i].features;
        c->name = api_strdup(ap1_classes[i].name);
        if (c->name == NULL) {
            return AP_ERR_OOM;
        }
        ctx->class_count++;
        while (*f != '\0') {
            const char *e = strchr(f, ',');
            size_t n = e == NULL ? strlen(f) : (size_t)(e - f);
            char *item = api_strndup(f, n);
            uint32_t id;
            if (item == NULL) {
                return AP_ERR_OOM;
            }
            st = api_context_label(ctx, item, &id);
            if (st == AP_OK) {
                api_labels_set(&c->labels, id);
            }
            free(item);
            if (st != AP_OK) {
                return st;
            }
            f += n;
            if (*f == ',') {
                f++;
            }
        }
        st = api_strmap_put(&ctx->class_index, c->name, (uint32_t)i);
        if (st != AP_OK) {
            return st;
        }
    }
    ctx->universe = (api_universe_entry *)calloc(ap1_universe_count, sizeof(api_universe_entry));
    if (ctx->universe == NULL) {
        return AP_ERR_OOM;
    }
    ctx->universe_count = ap1_universe_count;
    for (i = 0; i < ap1_universe_count; i++) {
        uint32_t existing;
        if (!api_strmap_get(&ctx->universe_index, ap1_universe[i], &existing)) {
            st = api_strmap_put(&ctx->universe_index, ap1_universe[i], (uint32_t)i);
            if (st != AP_OK) {
                return st;
            }
        }
    }
    ctx->seg_capacity = 64;
    ctx->segs = (ap_segment *)calloc(ctx->seg_capacity, sizeof(ap_segment));
    if (ctx->segs == NULL) {
        return AP_ERR_OOM;
    }
    ctx->segs[0].grapheme = api_strdup("#");
    if (ctx->segs[0].grapheme == NULL) {
        return AP_ERR_OOM;
    }
    ctx->seg_count = 1;
    return seg_table_grow(ctx);
}

void ap_context_free(ap_context *ctx)
{
    size_t i;

    if (ctx == NULL) {
        return;
    }
    for (i = 0; i < ctx->label_count; i++) {
        free(ctx->label_names[i]);
    }
    free(ctx->label_names);
    free(ctx->label_category);
    free(ctx->label_negates);
    api_strmap_free(&ctx->label_index);
    for (i = 0; i < ctx->category_count; i++) {
        free(ctx->category_names[i]);
    }
    free(ctx->category_names);
    for (i = 0; i < ctx->alias_count; i++) {
        free(ctx->alias_from[i]);
        free(ctx->alias_to[i]);
    }
    free(ctx->alias_from);
    free(ctx->alias_to);
    for (i = 0; i < ctx->class_count; i++) {
        free(ctx->classes[i].name);
    }
    free(ctx->classes);
    api_strmap_free(&ctx->class_index);
    for (i = 0; i < ctx->seg_count; i++) {
        free(ctx->segs[i].grapheme);
    }
    free(ctx->segs);
    free(ctx->seg_table);
    api_strmap_free(&ctx->universe_index);
    free(ctx->universe);
    free(ctx->reverse_table);
    free(ctx);
}

ap_status ap_context_new(
    const mk_system *system, const ap_context_options *options, ap_context **out, ap_diagnosis *diagnosis)
{
    ap_context *ctx;
    ap_status st;

    if (out == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    if (system == NULL) {
        api_diag(diagnosis, AP_ERR_INVALID_ARGUMENT, 0, "no merkmal system");
        return AP_ERR_INVALID_ARGUMENT;
    }
    ctx = (ap_context *)calloc(1, sizeof(ap_context));
    if (ctx == NULL) {
        return AP_ERR_OOM;
    }
    ctx->system = system;
    ap_context_options_init_defaults(&ctx->options);
    if (options != NULL) {
        ctx->options = *options;
    }
    if (ctx->options.projection != AP_PROJECTION_ALTERUPHONO_1) {
        api_diag(diagnosis, AP_ERR_INVALID_ARGUMENT, 0, "only the alteruphono-1 projection is implemented");
        free(ctx);
        return AP_ERR_INVALID_ARGUMENT;
    }
    st = context_init(ctx);
    if (st != AP_OK) {
        api_diag(diagnosis, st, 0, "cannot build the context: %s", ap_status_string(st));
        ap_context_free(ctx);
        return st;
    }
    *out = ctx;
    return AP_OK;
}

static char **copy_strings(char **src, size_t n, ap_status *st)
{
    char **dst = (char **)calloc(n + 1, sizeof(char *));
    size_t i;

    if (dst == NULL) {
        *st = AP_ERR_OOM;
        return NULL;
    }
    for (i = 0; i < n; i++) {
        dst[i] = api_strdup(src[i]);
        if (dst[i] == NULL) {
            *st = AP_ERR_OOM;
        }
    }
    return dst;
}

ap_status ap_context_clone(const ap_context *src, ap_context **out)
{
    ap_context *ctx;
    ap_status st = AP_OK;
    size_t i;

    if (src == NULL || out == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    ctx = (ap_context *)calloc(1, sizeof(ap_context));
    if (ctx == NULL) {
        return AP_ERR_OOM;
    }
    *ctx = *src;
    /* everything owned is deep-copied below; clear the borrowed pointers
     * first so that a failure frees only what this clone owns */
    ctx->label_names = NULL;
    ctx->label_category = NULL;
    ctx->label_negates = NULL;
    memset(&ctx->label_index, 0, sizeof(ctx->label_index));
    ctx->category_names = NULL;
    ctx->alias_from = NULL;
    ctx->alias_to = NULL;
    ctx->classes = NULL;
    memset(&ctx->class_index, 0, sizeof(ctx->class_index));
    ctx->segs = NULL;
    ctx->seg_table = NULL;
    memset(&ctx->universe_index, 0, sizeof(ctx->universe_index));
    ctx->universe = NULL;
    ctx->reverse_table = NULL;
    ctx->label_count = 0;
    ctx->category_count = 0;
    ctx->alias_count = 0;
    ctx->class_count = 0;
    ctx->seg_count = 0;

    ctx->label_names = copy_strings(src->label_names, src->label_count, &st);
    ctx->label_count = ctx->label_names != NULL ? src->label_count : 0;
    ctx->label_category = (int *)malloc((src->label_count + 1) * sizeof(int));
    ctx->label_negates = (int *)malloc((src->label_count + 1) * sizeof(int));
    ctx->category_names = copy_strings(src->category_names, src->category_count, &st);
    ctx->category_count = ctx->category_names != NULL ? src->category_count : 0;
    ctx->alias_from = copy_strings(src->alias_from, src->alias_count, &st);
    ctx->alias_to = copy_strings(src->alias_to, src->alias_count, &st);
    ctx->alias_count = (ctx->alias_from != NULL && ctx->alias_to != NULL) ? src->alias_count : 0;
    ctx->classes = (api_class *)calloc(src->class_count + 1, sizeof(api_class));
    ctx->segs = (ap_segment *)calloc(src->seg_capacity, sizeof(ap_segment));
    ctx->seg_table = (uint32_t *)malloc(src->seg_table_capacity * sizeof(uint32_t));
    ctx->universe = (api_universe_entry *)malloc((src->universe_count + 1) * sizeof(api_universe_entry));
    if (st != AP_OK || ctx->label_category == NULL || ctx->label_negates == NULL || ctx->classes == NULL || ctx->segs == NULL
        || ctx->seg_table == NULL || ctx->universe == NULL) {
        ap_context_free(ctx);
        return AP_ERR_OOM;
    }
    memcpy(ctx->label_category, src->label_category, src->label_count * sizeof(int));
    memcpy(ctx->label_negates, src->label_negates, src->label_count * sizeof(int));
    for (i = 0; i < src->class_count; i++) {
        ctx->classes[i] = src->classes[i];
        ctx->classes[i].name = api_strdup(src->classes[i].name);
        ctx->class_count++;
        if (ctx->classes[i].name == NULL) {
            st = AP_ERR_OOM;
        }
    }
    for (i = 0; i < src->seg_count; i++) {
        ctx->segs[i] = src->segs[i];
        ctx->segs[i].grapheme = api_strdup(src->segs[i].grapheme);
        ctx->seg_count++;
        if (ctx->segs[i].grapheme == NULL) {
            st = AP_ERR_OOM;
        }
    }
    memcpy(ctx->seg_table, src->seg_table, src->seg_table_capacity * sizeof(uint32_t));
    memcpy(ctx->universe, src->universe, src->universe_count * sizeof(api_universe_entry));
    ctx->reverse_built = 0; /* rebuilt lazily */
    if (st == AP_OK) {
        st = api_strmap_copy(&ctx->label_index, &src->label_index);
    }
    if (st == AP_OK) {
        st = api_strmap_copy(&ctx->class_index, &src->class_index);
    }
    if (st == AP_OK) {
        st = api_strmap_copy(&ctx->universe_index, &src->universe_index);
    }
    if (st != AP_OK) {
        ap_context_free(ctx);
        return st;
    }
    *out = ctx;
    return AP_OK;
}

/* ---- public segment calls ----------------------------------------------- */

ap_status ap_intern(ap_context *ctx, const char *grapheme, ap_seg *out)
{
    char *pre = NULL;
    ap_status st;

    if (ctx == NULL || grapheme == NULL || out == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    if (strcmp(grapheme, "#") == 0) {
        *out = AP_SEG_BOUNDARY;
        return AP_OK;
    }
    st = api_preprocess(grapheme, &pre);
    if (st != AP_OK) {
        return st;
    }
    st = api_make_sound(ctx, pre, out);
    free(pre);
    return st;
}

ap_status ap_seg_grapheme(const ap_context *ctx, ap_seg seg, const char **out)
{
    if (ctx == NULL || out == NULL || seg >= ctx->seg_count) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = ctx->segs[seg].grapheme;
    return AP_OK;
}

ap_status ap_seg_is_partial(const ap_context *ctx, ap_seg seg, int *out)
{
    if (ctx == NULL || out == NULL || seg >= ctx->seg_count) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = ctx->segs[seg].partial;
    return AP_OK;
}

static int cmp_str(const void *a, const void *b)
{
    return strcmp(*(const char *const *)a, *(const char *const *)b);
}

static ap_status labels_to_strings(const ap_context *ctx, const ap_labels *labels, char ***out, size_t *count)
{
    char **items = (char **)calloc(ctx->label_count + 1, sizeof(char *));
    size_t n = 0;
    size_t i;

    *out = NULL;
    *count = 0;
    if (items == NULL) {
        return AP_ERR_OOM;
    }
    for (i = 0; i < ctx->label_count; i++) {
        if (api_labels_has(labels, (uint32_t)i)) {
            items[n] = api_strdup(ctx->label_names[i]);
            if (items[n] == NULL) {
                api_free_parts(items, n);
                return AP_ERR_OOM;
            }
            n++;
        }
    }
    qsort(items, n, sizeof(char *), cmp_str);
    *out = items;
    *count = n;
    return AP_OK;
}

ap_status ap_seg_labels(const ap_context *ctx, ap_seg seg, char ***labels, size_t *count)
{
    if (ctx == NULL || labels == NULL || count == NULL || seg >= ctx->seg_count) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    return labels_to_strings(ctx, &ctx->segs[seg].labels, labels, count);
}

ap_status ap_grapheme_features(ap_context *ctx, const char *grapheme, char ***labels, size_t *count, int *found)
{
    ap_labels l;
    ap_status st;

    if (ctx == NULL || grapheme == NULL || labels == NULL || count == NULL || found == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *labels = NULL;
    *count = 0;
    st = api_lookup(ctx, grapheme, &l, found);
    if (st != AP_OK || !*found) {
        return st;
    }
    return labels_to_strings(ctx, &l, labels, count);
}

ap_status ap_features_grapheme(ap_context *ctx, const char *const *labels, size_t count, const char **out, int *found)
{
    ap_labels l;
    size_t i;

    if (ctx == NULL || (labels == NULL && count > 0) || out == NULL || found == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    *found = 0;
    memset(&l, 0, sizeof(l));
    for (i = 0; i < count; i++) {
        uint32_t id;
        if (!api_strmap_get(&ctx->label_index, labels[i], &id)) {
            return AP_OK; /* a label the universe never carries */
        }
        api_labels_set(&l, id);
    }
    {
        ap_status st = api_reverse(ctx, &l, out);
        *found = *out != NULL;
        return st;
    }
}
