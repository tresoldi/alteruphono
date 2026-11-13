/* The rule notation of alteruphono 1.x (parser.py), parsed by hand.
 *
 * Atom precedence is 1.x's, including its quirks: "!" before everything,
 * "{...}" before "|", a quantifier only after the back-reference forms, and
 * anything else a sound (a class name first, then a grapheme). */

#include "internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void api_tok_free_children(api_tok *tok)
{
    size_t i;

    if (tok == NULL) {
        return;
    }
    for (i = 0; i < tok->child_count; i++) {
        api_tok_free_children(&tok->children[i]);
    }
    free(tok->children);
    api_modifier_free(tok->modifier);
    tok->children = NULL;
    tok->child_count = 0;
    tok->modifier = NULL;
}

static api_modifier *modifier_copy(const api_modifier *m)
{
    api_modifier *c;

    if (m == NULL) {
        return NULL;
    }
    c = (api_modifier *)calloc(1, sizeof(api_modifier));
    if (c == NULL) {
        return NULL;
    }
    c->text = api_strdup(m->text);
    c->adds = (uint32_t *)malloc((m->add_count + 1) * sizeof(uint32_t));
    c->subs = (uint32_t *)malloc((m->sub_count + 1) * sizeof(uint32_t));
    if (c->text == NULL || c->adds == NULL || c->subs == NULL) {
        api_modifier_free(c);
        return NULL;
    }
    memcpy(c->adds, m->adds, m->add_count * sizeof(uint32_t));
    memcpy(c->subs, m->subs, m->sub_count * sizeof(uint32_t));
    c->add_count = m->add_count;
    c->sub_count = m->sub_count;
    return c;
}

ap_status api_tok_copy(const api_tok *src, api_tok *dst)
{
    size_t i;

    *dst = *src;
    dst->children = NULL;
    dst->child_count = 0;
    dst->modifier = NULL;
    if (src->modifier != NULL) {
        dst->modifier = modifier_copy(src->modifier);
        if (dst->modifier == NULL) {
            return AP_ERR_OOM;
        }
    }
    if (src->child_count > 0) {
        dst->children = (api_tok *)calloc(src->child_count, sizeof(api_tok));
        if (dst->children == NULL) {
            api_tok_free_children(dst);
            return AP_ERR_OOM;
        }
        for (i = 0; i < src->child_count; i++) {
            ap_status st = api_tok_copy(&src->children[i], &dst->children[i]);
            dst->child_count = i + 1;
            if (st != AP_OK) {
                api_tok_free_children(dst);
                return st;
            }
        }
    }
    return AP_OK;
}

static int ends_with(const char *s, size_t n, char c)
{
    return n > 0 && s[n - 1] == c;
}

static int is_ascii_digits(const char *s, size_t n)
{
    size_t i;

    if (n == 0) {
        return 0;
    }
    for (i = 0; i < n; i++) {
        if (s[i] < '0' || s[i] > '9') {
            return 0;
        }
    }
    return 1;
}

static long parse_index(const char *s, size_t n)
{
    long v = 0;
    size_t i;

    for (i = 0; i < n; i++) {
        if (v > 100000000L) {
            return v; /* absurd indices stay absurd; never overflow */
        }
        v = v * 10 + (s[i] - '0');
    }
    return v;
}

static ap_status parse_atom(ap_context *ctx, const char *atom, api_tok *out);

static ap_status parse_alternatives(ap_context *ctx, const char *text, size_t n, api_tok *out)
{
    /* 1.x: str.split("|"), then each part is an atom (stripped) */
    size_t parts = 1;
    size_t i;
    size_t start = 0;
    size_t k = 0;

    for (i = 0; i < n; i++) {
        if (text[i] == '|') {
            parts++;
        }
    }
    out->children = (api_tok *)calloc(parts, sizeof(api_tok));
    if (out->children == NULL) {
        return AP_ERR_OOM;
    }
    for (i = 0; i <= n; i++) {
        if (i == n || text[i] == '|') {
            char *part = api_strndup(text + start, i - start);
            ap_status st;
            if (part == NULL) {
                return AP_ERR_OOM;
            }
            st = parse_atom(ctx, part, &out->children[k]);
            free(part);
            out->child_count = ++k;
            if (st != AP_OK) {
                return st;
            }
            start = i + 1;
        }
    }
    return AP_OK;
}

static ap_status parse_atom(ap_context *ctx, const char *raw, api_tok *out)
{
    /* Atoms come from splitting preprocessed text on single spaces, so the
     * only whitespace 1.x's strip() could remove is none at all, except for
     * the parts of a choice, which cannot contain spaces either. */
    const char *atom = raw;
    size_t n = strlen(atom);
    ap_status st;

    memset(out, 0, sizeof(*out));
    if (n > 0 && atom[0] == '!') {
        out->kind = API_TOK_NEGATION;
        out->children = (api_tok *)calloc(1, sizeof(api_tok));
        if (out->children == NULL) {
            return AP_ERR_OOM;
        }
        out->child_count = 1;
        return parse_atom(ctx, atom + 1, &out->children[0]);
    }
    if (n > 0 && atom[0] == '{' && ends_with(atom, n, '}')) {
        out->kind = API_TOK_SET;
        /* 1.x: atom[1:-1]; for "{" alone that is "" */
        return parse_alternatives(ctx, atom + 1, n >= 2 ? n - 2 : 0, out);
    }
    if (memchr(atom, '|', n) != NULL) {
        out->kind = API_TOK_CHOICE;
        return parse_alternatives(ctx, atom, n, out);
    }
    if (strcmp(atom, "#") == 0) {
        out->kind = API_TOK_BOUNDARY;
        return AP_OK;
    }
    if (strcmp(atom, "_") == 0) {
        out->kind = API_TOK_FOCUS;
        return AP_OK;
    }
    if (strcmp(atom, ":null:") == 0) {
        out->kind = API_TOK_EMPTY;
        return AP_OK;
    }
    if (strcmp(atom, "_.onset") == 0 || strcmp(atom, "_.nucleus") == 0 || strcmp(atom, "_.coda") == 0) {
        out->kind = API_TOK_SYLLABLE;
        out->role = atom[2] == 'o' ? API_ROLE_ONSET : atom[2] == 'n' ? API_ROLE_NUCLEUS : API_ROLE_CODA;
        return AP_OK;
    }
    if (n >= 2 && atom[0] == '@') {
        /* ^@(\d+)\[([^\]]+)\]$  or  ^@(\d+)$ */
        const char *open = strchr(atom, '[');
        if (open == NULL && is_ascii_digits(atom + 1, n - 1)) {
            out->kind = API_TOK_BACKREF;
            out->index = parse_index(atom + 1, n - 1) - 1;
            return AP_OK;
        }
        if (open != NULL && is_ascii_digits(atom + 1, (size_t)(open - atom) - 1) && ends_with(atom, n, ']')) {
            size_t mlen = n - (size_t)(open - atom) - 2;
            const char *mtext = open + 1;
            if (mlen > 0 && memchr(mtext, ']', mlen) == NULL) {
                char *m = api_strndup(mtext, mlen);
                if (m == NULL) {
                    return AP_ERR_OOM;
                }
                out->kind = API_TOK_BACKREF;
                out->index = parse_index(atom + 1, (size_t)(open - atom) - 1) - 1;
                st = api_modifier_parse(ctx, m, &out->modifier);
                free(m);
                return st;
            }
        }
    }
    if (n > 1 && (atom[n - 1] == '+' || atom[n - 1] == '?')) {
        char *inner = api_strndup(atom, n - 1);
        if (inner == NULL) {
            return AP_ERR_OOM;
        }
        out->kind = API_TOK_QUANT;
        out->quantifier = atom[n - 1];
        out->children = (api_tok *)calloc(1, sizeof(api_tok));
        if (out->children == NULL) {
            free(inner);
            return AP_ERR_OOM;
        }
        out->child_count = 1;
        st = parse_atom(ctx, inner, &out->children[0]);
        free(inner);
        return st;
    }
    out->kind = API_TOK_SEGMENT;
    return api_make_sound(ctx, atom, &out->seg);
}

static void free_tokens(api_tok *toks, size_t n)
{
    size_t i;

    if (toks == NULL) {
        return;
    }
    for (i = 0; i < n; i++) {
        api_tok_free_children(&toks[i]);
    }
    free(toks);
}

static ap_status parse_atoms(ap_context *ctx, const char *text, size_t a, size_t b, api_tok **out, size_t *count)
{
    char **parts = NULL;
    size_t n = 0;
    size_t i;
    api_tok *toks;
    ap_status st = api_split(text, a, b, &parts, &n);

    *out = NULL;
    *count = 0;
    if (st != AP_OK) {
        return st;
    }
    toks = (api_tok *)calloc(n + 1, sizeof(api_tok));
    if (toks == NULL) {
        api_free_parts(parts, n);
        return AP_ERR_OOM;
    }
    for (i = 0; i < n && st == AP_OK; i++) {
        st = parse_atom(ctx, parts[i], &toks[i]);
    }
    api_free_parts(parts, n);
    if (st != AP_OK) {
        free_tokens(toks, i);
        return st;
    }
    *out = toks;
    *count = n;
    return AP_OK;
}

void ap_rule_free(ap_rule *rule)
{
    if (rule == NULL) {
        return;
    }
    free(rule->source);
    free_tokens(rule->ante, rule->ante_count);
    free_tokens(rule->post, rule->post_count);
    free(rule);
}

static size_t count_kind(const api_tok *toks, size_t n, api_tok_kind kind)
{
    size_t i;
    size_t c = 0;

    for (i = 0; i < n; i++) {
        if (toks[i].kind == kind) {
            c++;
        }
    }
    return c;
}

static int has_syllable(const api_tok *t)
{
    /* 1.x _needs_syllable_map looks at the top level only */
    return t->kind == API_TOK_SYLLABLE;
}

/* Finds the first code point among `stops` at or after byte `from`. */
static size_t find_cp(const char *s, size_t from, size_t len, const uint32_t *stops, size_t nstops)
{
    size_t i = from;

    while (i < len) {
        uint32_t cp;
        size_t k;
        size_t n = api_utf8_decode((const unsigned char *)s + i, len - i, &cp);
        for (k = 0; k < nstops; k++) {
            if (cp == stops[k]) {
                return i;
            }
        }
        i += n;
    }
    return len;
}

ap_status ap_rule_parse(ap_context *ctx, const char *text, ap_rule **out, ap_diagnosis *diag)
{
    static const uint32_t arrows[2] = { '>', 0x2192 };
    static const uint32_t slash[1] = { '/' };
    char *pre = NULL;
    ap_rule *rule = NULL;
    api_tok *ante = NULL;
    api_tok *post = NULL;
    api_tok *ctx_toks = NULL;
    size_t ante_n = 0;
    size_t post_n = 0;
    size_t ctx_n = 0;
    size_t len;
    size_t arrow;
    size_t arrow_len;
    size_t sl;
    int with_context;
    ap_status st;

    if (ctx == NULL || text == NULL || out == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    st = api_preprocess(text, &pre);
    if (st != AP_OK) {
        return st;
    }
    len = strlen(pre);
    /* ^([^>→]+)[>→]([^/]+)(/(.+))?$ */
    arrow = find_cp(pre, 0, len, arrows, 2);
    if (arrow == 0 || arrow >= len) {
        api_diag(diag, AP_ERR_PARSE, arrow, "Cannot parse rule: %s", text);
        free(pre);
        return AP_ERR_PARSE;
    }
    arrow_len = pre[arrow] == '>' ? 1 : 3;
    sl = find_cp(pre, arrow + arrow_len, len, slash, 1);
    with_context = sl < len;
    if (sl == arrow + arrow_len || (with_context && sl + 1 >= len)) {
        api_diag(diag, AP_ERR_PARSE, sl, "Cannot parse rule: %s", text);
        free(pre);
        return AP_ERR_PARSE;
    }

    st = parse_atoms(ctx, pre, 0, arrow, &ante, &ante_n);
    if (st == AP_OK) {
        st = parse_atoms(ctx, pre, arrow + arrow_len, sl, &post, &post_n);
    }
    if (st == AP_OK && count_kind(post, post_n, API_TOK_SET) > count_kind(ante, ante_n, API_TOK_SET)) {
        api_diag(diag, AP_ERR_PARSE, 0, "Set correspondence mismatch in rule %s", text);
        st = AP_ERR_PARSE;
    } else if (st == AP_OK && count_kind(post, post_n, API_TOK_CHOICE) > 0) {
        /* tresoldi/alteruphono 3fdb52b: an output must be one segment */
        api_diag(diag, AP_ERR_PARSE, 0, "Choice in the output of rule %s; use sets", text);
        st = AP_ERR_PARSE;
    }
    if (st == AP_OK && with_context) {
        st = parse_atoms(ctx, pre, sl + 1, len, &ctx_toks, &ctx_n);
    }
    rule = (ap_rule *)calloc(1, sizeof(ap_rule));
    if (st == AP_OK && rule == NULL) {
        st = AP_ERR_OOM;
    }
    if (st == AP_OK) {
        rule->source = api_strdup(text);
        if (rule->source == NULL) {
            st = AP_ERR_OOM;
        }
    }
    if (st == AP_OK && with_context) {
        size_t focus = ctx_n;
        size_t nfocus = 0;
        size_t i;
        size_t left;
        size_t right;
        for (i = 0; i < ctx_n; i++) {
            if (ctx_toks[i].kind == API_TOK_FOCUS) {
                nfocus++;
                focus = i;
            }
        }
        if (nfocus != 1) {
            api_diag(diag, AP_ERR_PARSE, sl, "Context must contain exactly one focus (_) in rule %s (found %zu)",
                text, nfocus);
            st = AP_ERR_PARSE;
        } else {
            left = focus;
            right = ctx_n - focus - 1;
            rule->ante = (api_tok *)calloc(left + ante_n + right + 1, sizeof(api_tok));
            rule->post = (api_tok *)calloc(left + post_n + right + 1, sizeof(api_tok));
            if (rule->ante == NULL || rule->post == NULL) {
                st = AP_ERR_OOM;
            } else {
                /* ante = left ++ ante ++ right; backrefs in ante/post shifted by
                 * len(left), those in the right context by len(left)+len(ante) */
                for (i = 0; i < left; i++) {
                    rule->ante[rule->ante_count++] = ctx_toks[i];
                    memset(&ctx_toks[i], 0, sizeof(api_tok));
                }
                for (i = 0; i < ante_n; i++) {
                    api_tok t = ante[i];
                    if (t.kind == API_TOK_BACKREF) {
                        t.index += (long)left;
                    }
                    rule->ante[rule->ante_count++] = t;
                    memset(&ante[i], 0, sizeof(api_tok));
                }
                for (i = focus + 1; i < ctx_n; i++) {
                    api_tok t = ctx_toks[i];
                    if (t.kind == API_TOK_BACKREF) {
                        t.index += (long)(left + ante_n);
                    }
                    rule->ante[rule->ante_count++] = t;
                    memset(&ctx_toks[i], 0, sizeof(api_tok));
                }
                for (i = 0; i < left; i++) {
                    api_tok *t = &rule->post[rule->post_count++];
                    t->kind = API_TOK_BACKREF;
                    t->index = (long)i;
                }
                for (i = 0; i < post_n; i++) {
                    api_tok t = post[i];
                    if (t.kind == API_TOK_BACKREF) {
                        t.index += (long)left;
                    }
                    rule->post[rule->post_count++] = t;
                    memset(&post[i], 0, sizeof(api_tok));
                }
                for (i = 0; i < right; i++) {
                    api_tok *t = &rule->post[rule->post_count++];
                    t->kind = API_TOK_BACKREF;
                    t->index = (long)(i + left + ante_n);
                }
                rule->left_len = left;
                rule->right_len = right;
            }
        }
    } else if (st == AP_OK) {
        rule->ante = ante;
        rule->ante_count = ante_n;
        rule->post = post;
        rule->post_count = post_n;
        ante = NULL;
        post = NULL;
        ante_n = 0;
        post_n = 0;
    }
    free_tokens(ante, ante_n);
    free_tokens(post, post_n);
    free_tokens(ctx_toks, ctx_n);
    free(pre);
    if (st != AP_OK) {
        ap_rule_free(rule);
        if (diag != NULL && diag->status == AP_OK) {
            api_diag(diag, st, 0, "%s", ap_status_string(st));
        }
        return st;
    }
    {
        size_t i;
        for (i = 0; i < rule->ante_count; i++) {
            if (rule->ante[i].kind == API_TOK_QUANT) {
                rule->has_quantifiers = 1;
            }
            if (has_syllable(&rule->ante[i])) {
                rule->has_syllable = 1;
            }
        }
    }
    *out = rule;
    return AP_OK;
}

ap_status ap_parse_sequence(
    ap_context *ctx, const char *text, ap_seg *buffer, size_t capacity, size_t *length, ap_diagnosis *diag)
{
    char *pre = NULL;
    char **parts = NULL;
    size_t n = 0;
    size_t i;
    ap_status st;

    if (ctx == NULL || text == NULL || length == NULL || (buffer == NULL && capacity > 0)) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *length = 0;
    st = api_preprocess(text, &pre);
    if (st == AP_OK) {
        st = api_split(pre, 0, strlen(pre), &parts, &n);
    }
    free(pre);
    if (st != AP_OK) {
        api_diag(diag, st, 0, "%s", ap_status_string(st));
        return st;
    }
    if (n > capacity) {
        api_free_parts(parts, n);
        *length = n;
        return AP_ERR_BUFFER_TOO_SMALL;
    }
    for (i = 0; i < n && st == AP_OK; i++) {
        if (strcmp(parts[i], "#") == 0) {
            buffer[i] = AP_SEG_BOUNDARY;
        } else {
            st = api_make_sound(ctx, parts[i], &buffer[i]);
        }
    }
    api_free_parts(parts, n);
    if (st != AP_OK) {
        return st;
    }
    *length = n;
    return AP_OK;
}

ap_status ap_render_sequence(const ap_context *ctx, const ap_seg *seq, size_t n, char **out)
{
    size_t total = 1;
    size_t i;
    char *buf;
    size_t w = 0;

    if (ctx == NULL || out == NULL || (seq == NULL && n > 0)) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    for (i = 0; i < n; i++) {
        if (seq[i] >= ctx->seg_count) {
            return AP_ERR_INVALID_ARGUMENT;
        }
        total += strlen(ctx->segs[seq[i]].grapheme) + 1;
    }
    buf = (char *)malloc(total);
    if (buf == NULL) {
        return AP_ERR_OOM;
    }
    for (i = 0; i < n; i++) {
        size_t len = strlen(ctx->segs[seq[i]].grapheme);
        if (i > 0) {
            buf[w++] = ' ';
        }
        memcpy(buf + w, ctx->segs[seq[i]].grapheme, len);
        w += len;
    }
    buf[w] = '\0';
    *out = buf;
    return AP_OK;
}

/* ---- JSON (the shape of 1.x's token dataclasses) -------------------------- */

typedef struct jbuf {
    char *s;
    size_t len;
    size_t cap;
    int oom;
} jbuf;

static void jput(jbuf *b, const char *s, size_t n)
{
    if (b->oom) {
        return;
    }
    if (b->len + n + 1 > b->cap) {
        size_t cap = b->cap == 0 ? 256 : b->cap;
        char *grown;
        while (b->len + n + 1 > cap) {
            cap *= 2;
        }
        grown = (char *)realloc(b->s, cap);
        if (grown == NULL) {
            b->oom = 1;
            return;
        }
        b->s = grown;
        b->cap = cap;
    }
    memcpy(b->s + b->len, s, n);
    b->len += n;
    b->s[b->len] = '\0';
}

static void jlit(jbuf *b, const char *s)
{
    jput(b, s, strlen(s));
}

static void jstr(jbuf *b, const char *s)
{
    static const char hex[] = "0123456789abcdef";
    const unsigned char *p = (const unsigned char *)s;

    jput(b, "\"", 1);
    for (; *p != '\0'; p++) {
        if (*p == '"' || *p == '\\') {
            char e[2] = { '\\', (char)*p };
            jput(b, e, 2);
        } else if (*p < 0x20) {
            char e[6] = { '\\', 'u', '0', '0', hex[*p >> 4], hex[*p & 15] };
            jput(b, e, 6);
        } else {
            jput(b, (const char *)p, 1);
        }
    }
    jput(b, "\"", 1);
}

static void jtok(jbuf *b, const ap_context *ctx, const api_tok *t)
{
    size_t i;
    char num[32];

    switch (t->kind) {
    case API_TOK_SEGMENT: {
        const ap_segment *s = api_seg(ctx, t->seg);
        char **labels = NULL;
        size_t n = 0;
        snprintf(num, sizeof(num), "%lu", (unsigned long)t->seg);
        jlit(b, "{\"kind\":\"segment\",\"id\":");
        jlit(b, num);
        jlit(b, ",\"grapheme\":");
        jstr(b, s->grapheme);
        jlit(b, ",\"features\":[");
        if (ap_seg_labels(ctx, t->seg, &labels, &n) != AP_OK) {
            b->oom = 1;
        }
        for (i = 0; i < n; i++) {
            if (i > 0) {
                jlit(b, ",");
            }
            jstr(b, labels[i]);
        }
        ap_strings_free(labels, n);
        jlit(b, s->partial ? "],\"partial\":true}" : "],\"partial\":false}");
        return;
    }
    case API_TOK_BOUNDARY:
        jlit(b, "{\"kind\":\"boundary\"}");
        return;
    case API_TOK_BACKREF:
        snprintf(num, sizeof(num), "%ld", t->index);
        jlit(b, "{\"kind\":\"backref\",\"index\":");
        jlit(b, num);
        jlit(b, ",\"modifier\":");
        if (t->modifier != NULL) {
            jstr(b, t->modifier->text);
        } else {
            jlit(b, "null");
        }
        jlit(b, "}");
        return;
    case API_TOK_EMPTY:
        jlit(b, "{\"kind\":\"empty\"}");
        return;
    case API_TOK_CHOICE:
    case API_TOK_SET:
        jlit(b, t->kind == API_TOK_CHOICE ? "{\"kind\":\"choice\",\"choices\":[" : "{\"kind\":\"set\",\"choices\":[");
        for (i = 0; i < t->child_count; i++) {
            if (i > 0) {
                jlit(b, ",");
            }
            jtok(b, ctx, &t->children[i]);
        }
        jlit(b, "]}");
        return;
    case API_TOK_FOCUS:
        jlit(b, "{\"kind\":\"focus\"}");
        return;
    case API_TOK_QUANT:
        jlit(b, t->quantifier == '+' ? "{\"kind\":\"quantified\",\"quantifier\":\"+\",\"inner\":"
                                     : "{\"kind\":\"quantified\",\"quantifier\":\"?\",\"inner\":");
        jtok(b, ctx, &t->children[0]);
        jlit(b, "}");
        return;
    case API_TOK_SYLLABLE:
        jlit(b, t->role == API_ROLE_ONSET ? "{\"kind\":\"syllable\",\"position\":\"onset\"}"
              : t->role == API_ROLE_NUCLEUS ? "{\"kind\":\"syllable\",\"position\":\"nucleus\"}"
                                            : "{\"kind\":\"syllable\",\"position\":\"coda\"}");
        return;
    case API_TOK_NEGATION:
        jlit(b, "{\"kind\":\"negation\",\"inner\":");
        jtok(b, ctx, &t->children[0]);
        jlit(b, "}");
        return;
    }
}

ap_status ap_rule_to_json(const ap_context *ctx, const ap_rule *rule, char **out)
{
    jbuf b = { NULL, 0, 0, 0 };
    char num[64];
    size_t i;

    if (ctx == NULL || rule == NULL || out == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    jlit(&b, "{\"source\":");
    jstr(&b, rule->source);
    snprintf(num, sizeof(num), ",\"left_len\":%zu,\"right_len\":%zu,\"ante\":[", rule->left_len, rule->right_len);
    jlit(&b, num);
    for (i = 0; i < rule->ante_count; i++) {
        if (i > 0) {
            jlit(&b, ",");
        }
        jtok(&b, ctx, &rule->ante[i]);
    }
    jlit(&b, "],\"post\":[");
    for (i = 0; i < rule->post_count; i++) {
        if (i > 0) {
            jlit(&b, ",");
        }
        jtok(&b, ctx, &rule->post[i]);
    }
    jlit(&b, "]}");
    if (b.oom) {
        free(b.s);
        return AP_ERR_OOM;
    }
    *out = b.s;
    return AP_OK;
}
