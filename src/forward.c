/* Forward application.
 *
 * Fixed-length rules follow alteruphono 1.x forward.py exactly: rules apply
 * simultaneously (SPE), both contexts are matched against the input and never
 * consumed.
 *
 * Quantified rules (+, ?) follow the same simultaneous semantics, which 1.x
 * meant but did not implement (docs/v2/DESIGN.md section 2, Q1 and Q2): at
 * each position the left context is matched backwards from it, and the focus
 * and right context forwards; `+` is greedy and `?` tries zero first, as in
 * 1.x's matcher; a back-reference to a quantified token stands for the last
 * element it matched. */

#include "internal.h"

#include <stdlib.h>
#include <string.h>

typedef struct fwd {
    ap_context *ctx;
    const ap_rule *rule;
    const ap_seg *seq;
    size_t n;
    const api_role *roles;
    size_t roles_len;
    api_segbuf *out;
} fwd;

static ap_status emit_post_token(
    fwd *f, const api_tok *tok, const ap_seg *elem_for_index /* NULL = absent */, size_t *set_cursor,
    const size_t *set_values, size_t set_count, int elem_present)
{
    ap_status st;

    switch (tok->kind) {
    case API_TOK_EMPTY:
        return AP_OK;
    case API_TOK_SEGMENT:
        return api_segbuf_push(f->out, tok->seg);
    case API_TOK_SET: {
        size_t idx;
        const api_tok *choice;
        if (*set_cursor >= set_count) {
            return AP_ERR_RULE; /* 1.x: ValueError, post uses more sets than ante */
        }
        idx = set_values[(*set_cursor)++];
        if (idx >= tok->child_count) {
            return AP_ERR_RULE;
        }
        choice = &tok->children[idx];
        if (choice->kind == API_TOK_SEGMENT) {
            return api_segbuf_push(f->out, choice->seg);
        }
        return AP_OK;
    }
    case API_TOK_BACKREF: {
        ap_seg out;
        if (!elem_present) {
            return AP_OK;
        }
        if (tok->modifier != NULL) {
            st = api_apply_backref_modifier(f->ctx, *elem_for_index, tok->modifier, &out);
            if (st != AP_OK) {
                return st;
            }
            return api_segbuf_push(f->out, out);
        }
        return api_segbuf_push(f->out, *elem_for_index);
    }
    case API_TOK_BOUNDARY:
        return api_segbuf_push(f->out, AP_SEG_BOUNDARY);
    case API_TOK_CHOICE:
    case API_TOK_FOCUS:
    case API_TOK_QUANT:
    case API_TOK_SYLLABLE:
    case API_TOK_NEGATION:
        return AP_OK; /* 1.x _translate has no branch for these: nothing */
    }
    return AP_OK;
}

static ap_status forward_fixed(fwd *f)
{
    const ap_rule *r = f->rule;
    size_t len_rule = r->ante_count;
    size_t left = r->left_len;
    size_t right = r->right_len;
    size_t focus_len = len_rule - left - right;
    size_t idx = 0;
    api_binding *b = (api_binding *)malloc((len_rule + 1) * sizeof(api_binding));
    size_t *sets = (size_t *)malloc((len_rule + 1) * sizeof(size_t));
    ap_status st = AP_OK;

    if (b == NULL || sets == NULL) {
        free(b);
        free(sets);
        return AP_ERR_OOM;
    }
    while (idx < f->n && st == AP_OK) {
        if (idx >= left && idx - left + len_rule <= f->n) {
            size_t start = idx - left;
            size_t i;
            int ok = 1;
            for (i = 0; i < len_rule; i++) {
                if (!api_match_one(f->ctx, f->seq[start + i], &r->ante[i], f->roles, f->roles_len, start + i, &b[i])) {
                    ok = 0;
                    break;
                }
            }
            if (ok) {
                size_t nsets = 0;
                size_t cursor = 0;
                for (i = 0; i < len_rule; i++) {
                    if (b[i].is_set) {
                        sets[nsets++] = b[i].set_index;
                    }
                }
                for (i = left; i + right < r->post_count && st == AP_OK; i++) {
                    const api_tok *t = &r->post[i];
                    long k = t->index;
                    int present = 0;
                    ap_seg elem = AP_SEG_BOUNDARY;
                    if (t->kind == API_TOK_BACKREF) {
                        /* 1.x: sub_seq[index] if index < len(sub_seq); Python
                         * indexing, so -1 (from "@0") is the last element */
                        if (k < 0) {
                            k += (long)len_rule;
                        }
                        if (k >= 0 && (size_t)k < len_rule) {
                            present = 1;
                            elem = f->seq[start + (size_t)k];
                        } else if (k < 0) {
                            st = AP_ERR_RULE;
                            break;
                        }
                    }
                    st = emit_post_token(f, t, &elem, &cursor, sets, nsets, present);
                }
                if (st != AP_OK) {
                    break;
                }
                if (focus_len > 0) {
                    idx += focus_len;
                } else {
                    st = api_segbuf_push(f->out, f->seq[idx]);
                    idx++;
                }
                continue;
            }
        }
        st = api_segbuf_push(f->out, f->seq[idx]);
        idx++;
    }
    free(b);
    free(sets);
    return st;
}

/* ---- quantified rules ---------------------------------------------------- */

typedef struct qmatch {
    fwd *f;
    size_t total;
    size_t left;
    size_t focus;          /* where the focus starts: the forward phase begins here */
    size_t *tok_start;     /* per ante token: first element matched */
    size_t *tok_count;     /* per ante token: elements matched */
    api_binding *elem_b;   /* per sequence position */
    size_t steps;
} qmatch;

#define Q_MAX_STEPS 1000000u

static int qm_one(qmatch *q, size_t pos, const api_tok *tok)
{
    return api_match_one(q->f->ctx, q->f->seq[pos], tok, q->f->roles, q->f->roles_len, pos, &q->elem_b[pos]);
}

/* Left phase: token ti (counting down), elements end before `edge`.
 * Forward phase: token ti (counting up), elements start at `edge`.
 * Returns 1 on success, 0 on failure, -1 when the step budget is spent. */
static int qm_rec(qmatch *q, int forward_phase, long ti, size_t edge)
{
    const api_tok *tok;
    const api_tok *inner;
    size_t avail;

    if (++q->steps > Q_MAX_STEPS) {
        return -1;
    }
    if (!forward_phase && ti < 0) {
        return qm_rec(q, 1, (long)q->left, q->focus);
    }
    if (forward_phase && (size_t)ti >= q->total) {
        return 1;
    }
    tok = &q->f->rule->ante[ti];
    avail = forward_phase ? q->f->n - edge : edge;
    inner = tok->kind == API_TOK_QUANT ? &tok->children[0] : tok;

    if (tok->kind == API_TOK_QUANT) {
        size_t k = 0;
        size_t take;
        int r;
        while (k < avail && qm_one(q, forward_phase ? edge + k : edge - 1 - k, inner)) {
            k++;
        }
        if (tok->quantifier == '?') {
            /* zero first, as 1.x's matcher */
            q->tok_count[ti] = 0;
            q->tok_start[ti] = edge;
            r = qm_rec(q, forward_phase, forward_phase ? ti + 1 : ti - 1, edge);
            if (r != 0) {
                return r;
            }
            if (k >= 1) {
                size_t p = forward_phase ? edge : edge - 1;
                qm_one(q, p, inner);
                q->tok_count[ti] = 1;
                q->tok_start[ti] = p;
                return qm_rec(q, forward_phase, forward_phase ? ti + 1 : ti - 1, forward_phase ? edge + 1 : edge - 1);
            }
            return 0;
        }
        for (take = k; take >= 1; take--) {
            size_t j;
            size_t start = forward_phase ? edge : edge - take;
            for (j = 0; j < take; j++) {
                qm_one(q, start + j, inner); /* re-establish bindings */
            }
            q->tok_count[ti] = take;
            q->tok_start[ti] = start;
            r = qm_rec(q, forward_phase, forward_phase ? ti + 1 : ti - 1, forward_phase ? edge + take : edge - take);
            if (r != 0) {
                return r;
            }
        }
        return 0;
    }
    if (avail == 0) {
        return 0;
    }
    {
        size_t p = forward_phase ? edge : edge - 1;
        if (!qm_one(q, p, tok)) {
            return 0;
        }
        q->tok_count[ti] = 1;
        q->tok_start[ti] = p;
        return qm_rec(q, forward_phase, forward_phase ? ti + 1 : ti - 1, forward_phase ? edge + 1 : edge - 1);
    }
}

static ap_status forward_quantified(fwd *f)
{
    const ap_rule *r = f->rule;
    qmatch q;
    size_t idx = 0;
    size_t *sets = NULL;
    ap_status st = AP_OK;

    memset(&q, 0, sizeof(q));
    q.f = f;
    q.total = r->ante_count;
    q.left = r->left_len;
    q.tok_start = (size_t *)calloc(q.total + 1, sizeof(size_t));
    q.tok_count = (size_t *)calloc(q.total + 1, sizeof(size_t));
    q.elem_b = (api_binding *)calloc(f->n + 1, sizeof(api_binding));
    sets = (size_t *)malloc((f->n + 1) * sizeof(size_t));
    if (q.tok_start == NULL || q.tok_count == NULL || q.elem_b == NULL || sets == NULL) {
        st = AP_ERR_OOM;
        goto done;
    }
    while (idx < f->n && st == AP_OK) {
        int m;
        q.steps = 0;
        q.focus = idx;
        m = qm_rec(&q, q.left == 0, q.left == 0 ? 0 : (long)q.left - 1, idx);
        if (m < 0) {
            st = AP_ERR_LIMIT;
            break;
        }
        if (m == 1) {
            size_t focus_count = 0;
            size_t nsets = 0;
            size_t cursor = 0;
            size_t t;
            size_t i;
            for (t = q.left; t + r->right_len < q.total; t++) {
                focus_count += q.tok_count[t];
            }
            for (t = 0; t < q.total; t++) {
                for (i = 0; i < q.tok_count[t]; i++) {
                    const api_binding *b = &q.elem_b[q.tok_start[t] + i];
                    if (b->is_set) {
                        sets[nsets++] = b->set_index;
                    }
                }
            }
            for (i = r->left_len; i + r->right_len < r->post_count && st == AP_OK; i++) {
                const api_tok *tok = &r->post[i];
                int present = 0;
                ap_seg elem = AP_SEG_BOUNDARY;
                if (tok->kind == API_TOK_BACKREF && tok->index >= 0 && (size_t)tok->index < q.total
                    && q.tok_count[tok->index] > 0) {
                    present = 1;
                    elem = f->seq[q.tok_start[tok->index] + q.tok_count[tok->index] - 1];
                }
                st = emit_post_token(f, tok, &elem, &cursor, sets, nsets, present);
            }
            if (st != AP_OK) {
                break;
            }
            if (focus_count > 0) {
                idx += focus_count;
            } else {
                st = api_segbuf_push(f->out, f->seq[idx]);
                idx++;
            }
            continue;
        }
        st = api_segbuf_push(f->out, f->seq[idx]);
        idx++;
    }
done:
    free(q.tok_start);
    free(q.tok_count);
    free(q.elem_b);
    free(sets);
    return st;
}

ap_status ap_forward(
    ap_context *ctx, const ap_rule *rule, const ap_seg *input, size_t length,
    ap_seg *output, size_t capacity, size_t *written)
{
    fwd f;
    api_segbuf out = { NULL, 0, 0 };
    api_role *roles = NULL;
    ap_status st;
    size_t i;

    if (ctx == NULL || rule == NULL || written == NULL || (input == NULL && length > 0)
        || (output == NULL && capacity > 0)) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *written = 0;
    for (i = 0; i < length; i++) {
        if (input[i] >= ctx->seg_count) {
            return AP_ERR_INVALID_ARGUMENT;
        }
    }
    if (rule->ante_count == 0 || length == 0) {
        if (length > capacity) {
            *written = length;
            return AP_ERR_BUFFER_TOO_SMALL;
        }
        if (length > 0) {
            memmove(output, input, length * sizeof(ap_seg));
        }
        *written = length;
        return AP_OK;
    }
    if (rule->has_syllable) {
        roles = (api_role *)malloc(length * sizeof(api_role));
        if (roles == NULL) {
            return AP_ERR_OOM;
        }
        st = api_syllable_roles(ctx, input, length, roles);
        if (st != AP_OK) {
            free(roles);
            return st;
        }
    }
    f.ctx = ctx;
    f.rule = rule;
    f.seq = input;
    f.n = length;
    f.roles = roles;
    f.roles_len = roles != NULL ? length : 0;
    f.out = &out;
    st = rule->has_quantifiers ? forward_quantified(&f) : forward_fixed(&f);
    free(roles);
    if (st == AP_OK) {
        if (out.count > capacity) {
            *written = out.count;
            st = AP_ERR_BUFFER_TOO_SMALL;
        } else {
            if (out.count > 0) {
                memcpy(output, out.items, out.count * sizeof(ap_seg));
            }
            *written = out.count;
        }
    }
    api_segbuf_free(&out);
    return st;
}
