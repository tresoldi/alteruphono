/* Backward reconstruction, as alteruphono 1.x backward.py with the fix of
 * tresoldi/alteruphono 3fdb52b: a choice or set the output does not resolve
 * stands for every one of its alternatives. */

#include "internal.h"

#include <stdlib.h>
#include <string.h>

struct ap_candidates {
    ap_seg **seqs;
    size_t *lengths;
    size_t count;
};

/* One reconstructed position: either an element, or a choice/set token of
 * the rule's ante (its alternatives are expanded at the end). */
typedef struct recon_item {
    int is_token;
    ap_seg seg;
    const api_tok *tok;
} recon_item;

typedef struct alt_list {
    ap_seg **options;     /* each option is a run of elements */
    size_t *option_len;
    size_t count;
} alt_list;

static void alt_free(alt_list *a)
{
    size_t i;

    for (i = 0; i < a->count; i++) {
        free(a->options[i]);
    }
    free(a->options);
    free(a->option_len);
    memset(a, 0, sizeof(*a));
}

static ap_status alt_add(alt_list *a, const ap_seg *run, size_t n)
{
    ap_seg **opts = (ap_seg **)realloc(a->options, (a->count + 1) * sizeof(ap_seg *));
    size_t *lens;

    if (opts == NULL) {
        return AP_ERR_OOM;
    }
    a->options = opts;
    lens = (size_t *)realloc(a->option_len, (a->count + 1) * sizeof(size_t));
    if (lens == NULL) {
        return AP_ERR_OOM;
    }
    a->option_len = lens;
    a->options[a->count] = (ap_seg *)malloc((n + 1) * sizeof(ap_seg));
    if (a->options[a->count] == NULL) {
        return AP_ERR_OOM;
    }
    if (n > 0) {
        memcpy(a->options[a->count], run, n * sizeof(ap_seg));
    }
    a->option_len[a->count] = n;
    a->count++;
    return AP_OK;
}

static long py_index(long index, size_t len, int *ok)
{
    if (index < 0) {
        index += (long)len;
    }
    *ok = index >= 0 && (size_t)index < len;
    return index;
}

/* 1.x _carry_backref_modifier */
static ap_status carry(ap_context *ctx, const api_tok *ante, const api_tok *post, api_tok *out)
{
    ap_status st = api_tok_copy(ante, out);
    const ap_segment *s;
    ap_labels labels;
    const char *g = NULL;
    char *norm = NULL;

    if (st != AP_OK || post->modifier == NULL || ante->kind != API_TOK_SEGMENT) {
        return st;
    }
    s = api_seg(ctx, ante->seg);
    if (api_labels_empty(&s->labels)) {
        return AP_OK;
    }
    api_apply_modifier(ctx, post->modifier, &s->labels, &labels);
    st = api_reverse(ctx, &labels, &g);
    if (st != AP_OK) {
        return st;
    }
    {
        int partial = s->partial;
        char *base = api_strdup(g != NULL ? g : s->grapheme);
        if (base == NULL) {
            return AP_ERR_OOM;
        }
        st = api_normalize_output(base, &norm);
        free(base);
        if (st != AP_OK) {
            return st;
        }
        st = api_intern_seg(ctx, norm, &labels, partial, &out->seg);
        free(norm);
    }
    return st;
}

/* 1.x invert step for a back-reference with a modifier */
static ap_status uncarry(ap_context *ctx, ap_seg elem, const api_modifier *m, ap_seg *out)
{
    api_modifier *inv = NULL;
    const ap_segment *s;
    ap_labels labels;
    const char *g = NULL;
    char *norm = NULL;
    char *base;
    ap_status st;

    *out = elem;
    if (elem == AP_SEG_BOUNDARY) {
        return AP_OK;
    }
    s = api_seg(ctx, elem);
    if (api_labels_empty(&s->labels)) {
        return AP_OK;
    }
    st = api_modifier_invert(ctx, m, &inv);
    if (st != AP_OK) {
        return st;
    }
    s = api_seg(ctx, elem); /* inverting may intern labels, not segments */
    api_apply_modifier(ctx, inv, &s->labels, &labels);
    api_modifier_free(inv);
    st = api_reverse(ctx, &labels, &g);
    if (st != AP_OK) {
        return st;
    }
    base = api_strdup(g != NULL ? g : api_seg(ctx, elem)->grapheme);
    if (base == NULL) {
        return AP_ERR_OOM;
    }
    st = api_normalize_output(base, &norm);
    free(base);
    if (st != AP_OK) {
        return st;
    }
    st = api_intern_seg(ctx, norm, &labels, 0, out);
    free(norm);
    return st;
}

/* 1.x _backward_translate: every reconstruction of one matched window */
static ap_status translate(
    ap_context *ctx, const ap_rule *rule, const ap_seg *sub, size_t sub_len,
    const api_binding *bindings, size_t nb, alt_list *alts)
{
    recon_item *recons = (recon_item *)calloc(rule->ante_count + 1, sizeof(recon_item));
    size_t *set_positions = (size_t *)malloc((rule->ante_count + 1) * sizeof(size_t));
    size_t nset = 0;
    size_t set_cursor = 0;
    size_t seq_idx = 0;
    size_t i;
    ap_status st = AP_OK;

    if (recons == NULL || set_positions == NULL) {
        free(recons);
        free(set_positions);
        return AP_ERR_OOM;
    }
    for (i = 0; i < rule->ante_count; i++) {
        const api_tok *t = &rule->ante[i];
        if (t->kind == API_TOK_SEGMENT) {
            recons[i].seg = t->seg;
        } else if (t->kind == API_TOK_CHOICE || t->kind == API_TOK_SET) {
            recons[i].is_token = 1;
            recons[i].tok = t;
            if (t->kind == API_TOK_SET) {
                set_positions[nset++] = i;
            }
        } else {
            recons[i].seg = AP_SEG_BOUNDARY; /* 1.x: Boundary for anything else */
        }
    }
    for (i = 0; i < rule->post_count && st == AP_OK; i++) {
        const api_tok *p = &rule->post[i];
        ap_seg elem;
        api_binding b;
        if (p->kind == API_TOK_EMPTY) {
            continue;
        }
        if (seq_idx >= sub_len || seq_idx >= nb) {
            break;
        }
        elem = sub[seq_idx];
        b = bindings[seq_idx];
        seq_idx++;
        if (p->kind == API_TOK_BACKREF) {
            int ok;
            long k = py_index(p->index, rule->ante_count, &ok);
            if (!ok) {
                st = AP_ERR_RULE; /* 1.x: IndexError */
                break;
            }
            recons[k].is_token = 0;
            recons[k].seg = elem;
            if (p->modifier != NULL) {
                st = uncarry(ctx, elem, p->modifier, &recons[k].seg);
            }
        } else if (p->kind == API_TOK_SET && b.is_set) {
            if (set_cursor < nset) {
                size_t at = set_positions[set_cursor++];
                const api_tok *set = &rule->ante[at];
                const api_tok *choice;
                if (b.set_index >= set->child_count) {
                    st = AP_ERR_RULE; /* 1.x: IndexError */
                    break;
                }
                choice = &set->children[b.set_index];
                if (choice->kind == API_TOK_SEGMENT) {
                    recons[at].is_token = 0;
                    recons[at].seg = choice->seg;
                }
            }
        }
    }
    if (st == AP_OK) {
        /* product over positions, last position varying fastest */
        size_t n = rule->ante_count;
        size_t *choice_count = (size_t *)calloc(n + 1, sizeof(size_t));
        size_t *odo = (size_t *)calloc(n + 1, sizeof(size_t));
        ap_seg *run = (ap_seg *)malloc((n + 1) * sizeof(ap_seg));
        size_t total = 1;
        if (choice_count == NULL || odo == NULL || run == NULL) {
            st = AP_ERR_OOM;
        } else {
            for (i = 0; i < n; i++) {
                size_t c = 1;
                if (recons[i].is_token) {
                    size_t j;
                    c = 0;
                    for (j = 0; j < recons[i].tok->child_count; j++) {
                        if (recons[i].tok->children[j].kind == API_TOK_SEGMENT) {
                            c++;
                        }
                    }
                    if (c == 0) {
                        c = 1; /* [Boundary()] */
                    }
                }
                choice_count[i] = c;
                if (total > ctx->options.max_backward_candidates / c) {
                    st = AP_ERR_LIMIT;
                }
                total *= c;
            }
            while (st == AP_OK) {
                for (i = 0; i < n; i++) {
                    if (!recons[i].is_token) {
                        run[i] = recons[i].seg;
                    } else {
                        size_t j;
                        size_t seen = 0;
                        run[i] = AP_SEG_BOUNDARY;
                        for (j = 0; j < recons[i].tok->child_count; j++) {
                            if (recons[i].tok->children[j].kind == API_TOK_SEGMENT) {
                                if (seen == odo[i]) {
                                    run[i] = recons[i].tok->children[j].seg;
                                    break;
                                }
                                seen++;
                            }
                        }
                    }
                }
                st = alt_add(alts, run, n);
                /* advance the odometer */
                i = n;
                while (i > 0) {
                    i--;
                    if (++odo[i] < choice_count[i]) {
                        break;
                    }
                    odo[i] = 0;
                    if (i == 0) {
                        i = n + 1; /* done */
                        break;
                    }
                }
                if (n == 0 || i == n + 1) {
                    break;
                }
            }
        }
        free(choice_count);
        free(odo);
        free(run);
    }
    free(recons);
    free(set_positions);
    return st;
}

void ap_candidates_free(ap_candidates *c)
{
    size_t i;

    if (c == NULL) {
        return;
    }
    for (i = 0; i < c->count; i++) {
        free(c->seqs[i]);
    }
    free(c->seqs);
    free(c->lengths);
    free(c);
}

size_t ap_candidates_count(const ap_candidates *c)
{
    return c == NULL ? 0 : c->count;
}

ap_status ap_candidates_get(const ap_candidates *c, size_t index, const ap_seg **seq, size_t *length)
{
    if (c == NULL || seq == NULL || length == NULL || index >= c->count) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *seq = c->seqs[index];
    *length = c->lengths[index];
    return AP_OK;
}

typedef struct cand_key {
    char *key;    /* " ".join(str(e)) */
    size_t order; /* position in product order */
    ap_seg *seq;
    size_t len;
} cand_key;

static int cmp_cand(const void *a, const void *b)
{
    const cand_key *x = (const cand_key *)a;
    const cand_key *y = (const cand_key *)b;
    int c = strcmp(x->key, y->key);

    if (c != 0) {
        return c;
    }
    return x->order < y->order ? -1 : x->order > y->order ? 1 : 0;
}

ap_status ap_backward(ap_context *ctx, const ap_rule *rule, const ap_seg *input, size_t length, ap_candidates **out)
{
    api_tok *post_ast = NULL;
    size_t len_post = 0;
    alt_list *alts = NULL;
    size_t nalts = 0;
    size_t idx = 0;
    size_t i;
    ap_status st = AP_OK;
    ap_candidates *res;
    cand_key *keys = NULL;
    size_t nkeys = 0;

    if (ctx == NULL || rule == NULL || out == NULL || (input == NULL && length > 0)) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    for (i = 0; i < length; i++) {
        if (input[i] >= ctx->seg_count) {
            return AP_ERR_INVALID_ARGUMENT;
        }
    }
    res = (ap_candidates *)calloc(1, sizeof(ap_candidates));
    if (res == NULL) {
        return AP_ERR_OOM;
    }
    post_ast = (api_tok *)calloc(rule->post_count + 1, sizeof(api_tok));
    if (post_ast == NULL) {
        free(res);
        return AP_ERR_OOM;
    }
    for (i = 0; i < rule->post_count && st == AP_OK; i++) {
        const api_tok *t = &rule->post[i];
        if (t->kind == API_TOK_EMPTY) {
            continue;
        }
        if (t->kind == API_TOK_BACKREF) {
            int ok;
            long k = py_index(t->index, rule->ante_count, &ok);
            if (!ok) {
                st = AP_ERR_RULE; /* 1.x: IndexError */
                break;
            }
            st = carry(ctx, &rule->ante[k], t, &post_ast[len_post]);
        } else {
            st = api_tok_copy(t, &post_ast[len_post]);
        }
        len_post++;
    }
    if (st == AP_OK && (len_post == 0 || length == 0)) {
        res->seqs = (ap_seg **)malloc(sizeof(ap_seg *));
        res->lengths = (size_t *)malloc(sizeof(size_t));
        if (res->seqs == NULL || res->lengths == NULL) {
            st = AP_ERR_OOM;
        } else {
            res->seqs[0] = (ap_seg *)malloc((length + 1) * sizeof(ap_seg));
            if (res->seqs[0] == NULL) {
                st = AP_ERR_OOM;
            } else {
                if (length > 0) {
                    memcpy(res->seqs[0], input, length * sizeof(ap_seg));
                }
                res->lengths[0] = length;
                res->count = 1;
            }
        }
        goto finish;
    }
    alts = (alt_list *)calloc(length + 1, sizeof(alt_list));
    if (st == AP_OK && alts == NULL) {
        st = AP_ERR_OOM;
    }
    while (st == AP_OK && idx < length) {
        if (idx + len_post <= length) {
            int matched = 0;
            api_binding *b = NULL;
            size_t nb = 0;
            st = api_match_pattern(ctx, input + idx, len_post, post_ast, len_post, &matched, &b, &nb);
            if (st == AP_OK && matched) {
                st = alt_add(&alts[nalts], input + idx, len_post);
                if (st == AP_OK) {
                    st = translate(ctx, rule, input + idx, len_post, b, nb, &alts[nalts]);
                }
                free(b);
                nalts++;
                idx += len_post;
                continue;
            }
            free(b);
        }
        if (st == AP_OK) {
            st = alt_add(&alts[nalts], input + idx, 1);
            nalts++;
            idx++;
        }
    }
    if (st == AP_OK) {
        /* the product of the alternatives */
        size_t total = 1;
        size_t *odo = (size_t *)calloc(nalts + 1, sizeof(size_t));
        size_t maxlen = 0;
        ap_seg *flat = NULL;
        for (i = 0; i < nalts; i++) {
            size_t j;
            size_t m = 0;
            if (total > ctx->options.max_backward_candidates / alts[i].count) {
                st = AP_ERR_LIMIT;
            }
            total *= alts[i].count;
            for (j = 0; j < alts[i].count; j++) {
                if (alts[i].option_len[j] > m) {
                    m = alts[i].option_len[j];
                }
            }
            maxlen += m;
        }
        if (st == AP_OK) {
            flat = (ap_seg *)malloc((maxlen + 1) * sizeof(ap_seg));
            keys = (cand_key *)calloc(total + 1, sizeof(cand_key));
            if (odo == NULL || flat == NULL || keys == NULL) {
                st = AP_ERR_OOM;
            }
        }
        while (st == AP_OK) {
            size_t len = 0;
            int interior_boundary = 0;
            for (i = 0; i < nalts; i++) {
                memcpy(flat + len, alts[i].options[odo[i]], alts[i].option_len[odo[i]] * sizeof(ap_seg));
                len += alts[i].option_len[odo[i]];
            }
            if (len >= 3) {
                for (i = 1; i + 1 < len; i++) {
                    if (flat[i] == AP_SEG_BOUNDARY) {
                        interior_boundary = 1;
                        break;
                    }
                }
            }
            if (!interior_boundary) {
                char *key = NULL;
                st = ap_render_sequence(ctx, flat, len, &key);
                if (st == AP_OK) {
                    keys[nkeys].key = key;
                    keys[nkeys].order = nkeys;
                    keys[nkeys].len = len;
                    keys[nkeys].seq = (ap_seg *)malloc((len + 1) * sizeof(ap_seg));
                    if (keys[nkeys].seq == NULL) {
                        free(key);
                        st = AP_ERR_OOM;
                    } else {
                        if (len > 0) {
                            memcpy(keys[nkeys].seq, flat, len * sizeof(ap_seg));
                        }
                        nkeys++;
                    }
                }
            }
            /* odometer, last fastest */
            i = nalts;
            while (i > 0) {
                i--;
                if (++odo[i] < alts[i].count) {
                    break;
                }
                odo[i] = 0;
                if (i == 0) {
                    i = nalts + 1;
                    break;
                }
            }
            if (nalts == 0 || i == nalts + 1) {
                break;
            }
        }
        free(odo);
        free(flat);
    }
    if (st == AP_OK) {
        /* dedupe on the rendered key (1.x: tuple of str, first kept), then sort
         * by the joined string, stably */
        size_t w = 0;
        qsort(keys, nkeys, sizeof(cand_key), cmp_cand);
        for (i = 0; i < nkeys; i++) {
            if (w > 0 && strcmp(keys[w - 1].key, keys[i].key) == 0) {
                free(keys[i].key);
                free(keys[i].seq);
                continue;
            }
            keys[w++] = keys[i];
        }
        nkeys = w;
        res->seqs = (ap_seg **)calloc(nkeys + 1, sizeof(ap_seg *));
        res->lengths = (size_t *)calloc(nkeys + 1, sizeof(size_t));
        if (res->seqs == NULL || res->lengths == NULL) {
            st = AP_ERR_OOM;
        } else {
            for (i = 0; i < nkeys; i++) {
                res->seqs[i] = keys[i].seq;
                res->lengths[i] = keys[i].len;
                keys[i].seq = NULL;
                free(keys[i].key);
                keys[i].key = NULL;
            }
            res->count = nkeys;
            nkeys = 0;
        }
    }
finish:
    for (i = 0; i < nkeys; i++) {
        free(keys[i].key);
        free(keys[i].seq);
    }
    free(keys);
    if (alts != NULL) {
        for (i = 0; i < length + 1; i++) {
            alt_free(&alts[i]);
        }
        free(alts);
    }
    for (i = 0; i < len_post; i++) {
        api_tok_free_children(&post_ast[i]);
    }
    free(post_ast);
    if (st != AP_OK) {
        ap_candidates_free(res);
        return st;
    }
    *out = res;
    return AP_OK;
}
