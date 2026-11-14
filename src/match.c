/* Matching, as alteruphono 1.x match.py, and its syllabifier (prosody.py). */

#include "internal.h"

#include <stdlib.h>
#include <string.h>

static int match_segment(const ap_context *ctx, ap_seg elem, ap_seg pattern)
{
    const ap_segment *e;
    const ap_segment *p;

    if (elem == AP_SEG_BOUNDARY) {
        return 0;
    }
    e = api_seg(ctx, elem);
    p = api_seg(ctx, pattern);
    if (!p->partial) {
        return elem == pattern || strcmp(e->grapheme, p->grapheme) == 0;
    }
    if (api_labels_empty(&p->labels) || api_labels_empty(&e->labels)) {
        return 0;
    }
    return api_labels_subset(&p->positive, &e->labels) && !api_labels_intersect(&p->negative, &e->labels);
}

int api_match_one(
    const ap_context *ctx, ap_seg elem, const api_tok *tok,
    const api_role *roles, size_t roles_len, size_t position, api_binding *out)
{
    size_t i;
    api_binding scratch;

    out->is_set = 0;
    out->seg = elem;
    out->set_index = 0;
    switch (tok->kind) {
    case API_TOK_BOUNDARY:
        return elem == AP_SEG_BOUNDARY;
    case API_TOK_SEGMENT:
        return match_segment(ctx, elem, tok->seg);
    case API_TOK_CHOICE:
        for (i = 0; i < tok->child_count; i++) {
            if (api_match_one(ctx, elem, &tok->children[i], roles, roles_len, position, &scratch)) {
                return 1;
            }
        }
        return 0;
    case API_TOK_SET:
        for (i = 0; i < tok->child_count; i++) {
            if (api_match_one(ctx, elem, &tok->children[i], roles, roles_len, position, &scratch)) {
                out->is_set = 1;
                out->set_index = i;
                return 1;
            }
        }
        return 0;
    case API_TOK_SYLLABLE:
        return roles != NULL && position < roles_len && roles[position] != API_ROLE_NONE
            && roles[position] == tok->role;
    case API_TOK_NEGATION:
        return !api_match_one(ctx, elem, &tok->children[0], roles, roles_len, position, &scratch);
    case API_TOK_BACKREF:
    case API_TOK_EMPTY:
    case API_TOK_FOCUS:
    case API_TOK_QUANT:
        return 0;
    }
    return 0;
}

/* ---- 1.x match_pattern (used by backward) -------------------------------- */

typedef struct bt_state {
    const ap_context *ctx;
    const ap_seg *seq;
    size_t n;
    const api_tok *pattern;
    size_t plen;
    api_binding *stack;    /* bindings so far */
    size_t depth;
    size_t steps;
} bt_state;

#define BT_MAX_STEPS 1000000u

/* Returns 1 on success (stack[0..depth) are the bindings), 0 on failure,
 * -1 when the step budget is exhausted. */
static int backtrack(bt_state *s, size_t seq_idx, size_t pat_idx)
{
    const api_tok *tok;
    api_binding b;

    if (++s->steps > BT_MAX_STEPS) {
        return -1;
    }
    if (pat_idx >= s->plen) {
        return 1;
    }
    tok = &s->pattern[pat_idx];
    if (tok->kind == API_TOK_QUANT && tok->quantifier == '+') {
        size_t base = s->depth;
        size_t k = 0;
        size_t idx = seq_idx;
        size_t take;
        while (idx < s->n && api_match_one(s->ctx, s->seq[idx], &tok->children[0], NULL, 0, idx, &b)) {
            s->stack[base + k] = b;
            k++;
            idx++;
        }
        for (take = k; take >= 1; take--) {
            int r;
            size_t j;
            /* the greedy prefix is re-established: deeper calls may have
             * overwritten stack entries beyond base + take */
            for (j = 0; j < take; j++) {
                api_match_one(s->ctx, s->seq[seq_idx + j], &tok->children[0], NULL, 0, seq_idx + j, &s->stack[base + j]);
            }
            s->depth = base + take;
            r = backtrack(s, seq_idx + take, pat_idx + 1);
            if (r != 0) {
                return r;
            }
        }
        s->depth = base;
        return 0;
    }
    if (tok->kind == API_TOK_QUANT && tok->quantifier == '?') {
        size_t base = s->depth;
        int r = backtrack(s, seq_idx, pat_idx + 1);
        if (r != 0) {
            return r;
        }
        s->depth = base;
        if (seq_idx < s->n && api_match_one(s->ctx, s->seq[seq_idx], &tok->children[0], NULL, 0, seq_idx, &b)) {
            s->stack[s->depth++] = b;
            r = backtrack(s, seq_idx + 1, pat_idx + 1);
            if (r != 0) {
                return r;
            }
        }
        s->depth = base;
        return 0;
    }
    if (seq_idx >= s->n) {
        return 0;
    }
    if (!api_match_one(s->ctx, s->seq[seq_idx], tok, NULL, 0, seq_idx, &b)) {
        return 0;
    }
    {
        size_t base = s->depth;
        int r;
        s->stack[s->depth++] = b;
        r = backtrack(s, seq_idx + 1, pat_idx + 1);
        if (r == 0) {
            s->depth = base;
        }
        return r;
    }
}

ap_status api_match_pattern(
    const ap_context *ctx, const ap_seg *seq, size_t n,
    const api_tok *pattern, size_t plen,
    int *matched, api_binding **bindings, size_t *count)
{
    size_t i;
    int quantified = 0;
    api_binding *out;

    *matched = 0;
    *bindings = NULL;
    *count = 0;
    for (i = 0; i < plen; i++) {
        if (pattern[i].kind == API_TOK_QUANT) {
            quantified = 1;
        }
    }
    out = (api_binding *)calloc(n + plen + 1, sizeof(api_binding));
    if (out == NULL) {
        return AP_ERR_OOM;
    }
    if (!quantified) {
        int all = n == plen;
        if (all) {
            for (i = 0; i < n; i++) {
                if (!api_match_one(ctx, seq[i], &pattern[i], NULL, 0, i, &out[i])) {
                    all = 0;
                    break;
                }
            }
        }
        if (all) {
            *matched = 1;
            *bindings = out;
            *count = n;
            return AP_OK;
        }
        free(out);
        return AP_OK;
    }
    {
        bt_state s;
        int r;
        s.ctx = ctx;
        s.seq = seq;
        s.n = n;
        s.pattern = pattern;
        s.plen = plen;
        s.stack = out;
        s.depth = 0;
        s.steps = 0;
        r = backtrack(&s, 0, 0);
        if (r < 0) {
            free(out);
            return AP_ERR_LIMIT;
        }
        if (r == 1) {
            *matched = 1;
            *bindings = out;
            *count = s.depth;
            return AP_OK;
        }
    }
    free(out);
    return AP_OK;
}

/* ---- syllables (prosody.py, default constraints) ------------------------- */

typedef struct sono_labels {
    int ok;
    uint32_t scale[11];
    int level[11];
    uint32_t syllabic;
    uint32_t consonant;
    uint32_t vowel;
} sono_labels;

static void sono_init(const ap_context *ctx, sono_labels *s)
{
    static const char *const names[11] = {
        "vowel", "approximant", "lateral", "trill", "tap", "nasal",
        "fricative", "affricate", "stop", "click", "implosive"
    };
    static const int levels[11] = { 5, 4, 4, 3, 3, 2, 1, 0, 0, 0, 0 };
    size_t i;

    s->ok = 1;
    for (i = 0; i < 11; i++) {
        s->level[i] = levels[i];
        if (!api_strmap_get(&ctx->label_index, names[i], &s->scale[i])) {
            s->ok = 0;
        }
    }
    if (!api_strmap_get(&ctx->label_index, "syllabic", &s->syllabic)
        || !api_strmap_get(&ctx->label_index, "consonant", &s->consonant)
        || !api_strmap_get(&ctx->label_index, "vowel", &s->vowel)) {
        s->ok = 0;
    }
}

static ap_status sound_features(ap_context *ctx, ap_seg seg, ap_labels *out)
{
    const ap_segment *s = api_seg(ctx, seg);
    int found;

    if (!api_labels_empty(&s->labels)) {
        *out = s->labels;
        return AP_OK;
    }
    {
        char *g = api_strdup(s->grapheme);
        ap_status st;
        if (g == NULL) {
            return AP_ERR_OOM;
        }
        st = api_lookup(ctx, g, out, &found);
        free(g);
        if (st == AP_OK && !found) {
            memset(out, 0, sizeof(*out));
        }
        return st;
    }
}

static int sonority(const sono_labels *s, const ap_labels *f)
{
    size_t i;

    for (i = 0; i < 11; i++) {
        if (api_labels_has(f, s->scale[i])) {
            return s->level[i];
        }
    }
    if (api_labels_has(f, s->syllabic)) {
        return 5;
    }
    return 0;
}

static int legal_onset(const sono_labels *s, const int *son, size_t a, size_t b)
{
    size_t i;

    if (b - a <= 1) {
        return 1;
    }
    if (b - a > 3) {
        return 0;
    }
    for (i = a; i + 1 < b; i++) {
        if (son[i + 1] <= son[i]) {
            return 0;
        }
    }
    (void)s;
    return 1;
}

ap_status api_syllable_roles(ap_context *ctx, const ap_seg *seq, size_t n, api_role *roles)
{
    sono_labels sl;
    size_t *pos = NULL;      /* sequence index of each sound */
    int *son = NULL;
    int *nuc = NULL;
    size_t *ns = NULL;       /* nucleus start, end (inclusive) */
    size_t *ne = NULL;
    api_role *assigned = NULL;
    size_t m = 0;
    size_t nn = 0;
    size_t na = 0;
    size_t i;
    ap_status st = AP_OK;

    for (i = 0; i < n; i++) {
        roles[i] = API_ROLE_NONE;
    }
    sono_init(ctx, &sl);
    if (!sl.ok) {
        return AP_OK;
    }
    pos = (size_t *)malloc((n + 1) * sizeof(size_t));
    son = (int *)malloc((n + 1) * sizeof(int));
    nuc = (int *)malloc((n + 1) * sizeof(int));
    ns = (size_t *)malloc((n + 1) * sizeof(size_t));
    ne = (size_t *)malloc((n + 1) * sizeof(size_t));
    assigned = (api_role *)malloc((n + 1) * sizeof(api_role));
    if (pos == NULL || son == NULL || nuc == NULL || ns == NULL || ne == NULL || assigned == NULL) {
        st = AP_ERR_OOM;
        goto done;
    }
    for (i = 0; i < n; i++) {
        ap_labels f;
        if (seq[i] == AP_SEG_BOUNDARY) {
            continue;
        }
        st = sound_features(ctx, seq[i], &f);
        if (st != AP_OK) {
            goto done;
        }
        pos[m] = i;
        son[m] = sonority(&sl, &f);
        nuc[m] = api_labels_has(&f, sl.vowel)
            || (api_labels_has(&f, sl.syllabic) && !api_labels_has(&f, sl.consonant));
        m++;
    }
    if (m == 0) {
        goto done;
    }
    /* nuclei: runs of vowels, split where sonority rises (hiatus) */
    i = 0;
    while (i < m) {
        if (nuc[i]) {
            size_t start = i;
            i++;
            while (i < m && nuc[i]) {
                if (son[i] > son[i - 1]) {
                    break;
                }
                i++;
            }
            ns[nn] = start;
            ne[nn] = i - 1;
            nn++;
        } else {
            i++;
        }
    }
    if (nn == 0) {
        for (i = 0; i < m; i++) {
            assigned[na++] = API_ROLE_ONSET;
        }
    } else {
        /* Build syllables as role runs: onset, nucleus, coda. A previous
         * syllable's coda is appended later, so keep run lengths per syllable. */
        size_t *on_len = (size_t *)calloc(nn, sizeof(size_t));
        size_t *co_len = (size_t *)calloc(nn, sizeof(size_t));
        size_t k;
        if (on_len == NULL || co_len == NULL) {
            free(on_len);
            free(co_len);
            st = AP_ERR_OOM;
            goto done;
        }
        for (k = 0; k < nn; k++) {
            if (k == 0) {
                on_len[k] = ns[0];
            } else {
                size_t a = ne[k - 1] + 1;
                size_t b = ns[k];
                if (b > a) {
                    size_t split = b - a;
                    size_t sa;
                    size_t coda;
                    for (sa = 0; sa <= b - a; sa++) {
                        if (legal_onset(&sl, son, a + sa, b)) {
                            split = sa;
                            break;
                        }
                    }
                    coda = split;
                    if (coda > 3) {
                        coda = 3; /* 1.x keeps prev_coda[-3:] and drops the rest */
                    }
                    co_len[k - 1] += coda;
                    on_len[k] = (b - a) - split;
                }
            }
            if (k == nn - 1) {
                co_len[k] += m - (ne[k] + 1);
            }
        }
        for (k = 0; k < nn; k++) {
            size_t j;
            for (j = 0; j < on_len[k]; j++) {
                assigned[na++] = API_ROLE_ONSET;
            }
            for (j = ns[k]; j <= ne[k]; j++) {
                assigned[na++] = API_ROLE_NUCLEUS;
            }
            for (j = 0; j < co_len[k]; j++) {
                assigned[na++] = API_ROLE_CODA;
            }
        }
        free(on_len);
        free(co_len);
    }
    /* 1.x build_syllable_map: roles go to the sounds in order */
    for (i = 0; i < na && i < m; i++) {
        roles[pos[i]] = assigned[i];
    }
done:
    free(pos);
    free(son);
    free(nuc);
    free(ns);
    free(ne);
    free(assigned);
    return st;
}
