/* The change model's scorer: the C port of alteruphono/model/fit.py's
 * linear predictor, for a pack exported by alteruphono/model/pack.py. */

#include "internal.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define AP_MODEL_MAGIC "alteruphono-change-model"

typedef struct cat_entry {
    char **reflex;
    double *weight;
    size_t count;
} cat_entry;

struct ap_model {
    const ap_context *ctx;
    size_t width;
    int vocoid;
    double a_sub, a_del, beta, lam;
    double *g_sub, *g_del, *w_up, *w_down, *z_left, *z_right;
    double v_sub[4], v_del[4];
    ap_rule **rules;
    double *rule_weight;
    size_t rule_count;
    /* caches */
    api_strmap vec_index;
    double *vecs;
    size_t vec_count, vec_cap;
    api_strmap dist_index;
    double *dists;
    size_t dist_count, dist_cap;
    api_strmap cat_index;
    cat_entry *cats;
    size_t cat_count, cat_cap;
};

void ap_model_free(ap_model *m)
{
    size_t i;
    size_t j;

    if (m == NULL) {
        return;
    }
    free(m->g_sub);
    free(m->g_del);
    free(m->w_up);
    free(m->w_down);
    free(m->z_left);
    free(m->z_right);
    for (i = 0; i < m->rule_count; i++) {
        ap_rule_free(m->rules[i]);
    }
    free(m->rules);
    free(m->rule_weight);
    api_strmap_free(&m->vec_index);
    free(m->vecs);
    api_strmap_free(&m->dist_index);
    free(m->dists);
    api_strmap_free(&m->cat_index);
    for (i = 0; i < m->cat_count; i++) {
        for (j = 0; j < m->cats[i].count; j++) {
            free(m->cats[i].reflex[j]);
        }
        free(m->cats[i].reflex);
        free(m->cats[i].weight);
    }
    free(m->cats);
    free(m);
}

/* ---- loading ------------------------------------------------------------- */

static char *next_line(const char **p, const char *end)
{
    const char *s = *p;
    const char *e = s;

    if (s >= end) {
        return NULL;
    }
    while (e < end && *e != '\n') {
        e++;
    }
    *p = e < end ? e + 1 : end;
    return api_strndup(s, (size_t)(e - s));
}

static int label_index(char **labels, size_t n, const char *name, size_t len)
{
    size_t i;

    for (i = 0; i < n; i++) {
        if (strlen(labels[i]) == len && strncmp(labels[i], name, len) == 0) {
            return (int)i;
        }
    }
    return -1;
}

static ap_status set_param(ap_model *m, char **labels, const char *name, double v)
{
    static const char *const env[4] = { "L=#", "L=V", "R=#", "R=V" };
    const char *colon;
    int k;

    if (strcmp(name, "a_sub") == 0) { m->a_sub = v; return AP_OK; }
    if (strcmp(name, "a_del") == 0) { m->a_del = v; return AP_OK; }
    if (strcmp(name, "beta") == 0) { m->beta = v; return AP_OK; }
    if (strcmp(name, "lam") == 0) { m->lam = v; return AP_OK; }
    if (strncmp(name, "alpha:", 6) == 0) {
        return AP_OK; /* fitted branches; prediction takes an explicit offset */
    }
    if (strncmp(name, "v_sub:", 6) == 0 || strncmp(name, "v_del:", 6) == 0) {
        for (k = 0; k < 4; k++) {
            if (strcmp(name + 6, env[k]) == 0) {
                (name[2] == 's' ? m->v_sub : m->v_del)[k] = v;
                return AP_OK;
            }
        }
        return AP_ERR_MODEL_FORMAT;
    }
    if (strncmp(name, "g_sub:", 6) == 0 || strncmp(name, "g_del:", 6) == 0) {
        k = label_index(labels, m->width, name + 6, strlen(name + 6));
        if (k < 0) {
            return AP_ERR_MODEL_FORMAT;
        }
        (name[2] == 's' ? m->g_sub : m->g_del)[k] = v;
        return AP_OK;
    }
    if (strncmp(name, "w:", 2) == 0 || strncmp(name, "z:", 2) == 0) {
        colon = strrchr(name, ':');
        if (colon == NULL || colon == name + 1) {
            return AP_ERR_MODEL_FORMAT;
        }
        k = label_index(labels, m->width, name + 2, (size_t)(colon - name - 2));
        if (k < 0) {
            return AP_ERR_MODEL_FORMAT;
        }
        if (name[0] == 'w' && strcmp(colon + 1, "up") == 0) { m->w_up[k] = v; return AP_OK; }
        if (name[0] == 'w' && strcmp(colon + 1, "down") == 0) { m->w_down[k] = v; return AP_OK; }
        if (name[0] == 'z' && strcmp(colon + 1, "left") == 0) { m->z_left[k] = v; return AP_OK; }
        if (name[0] == 'z' && strcmp(colon + 1, "right") == 0) { m->z_right[k] = v; return AP_OK; }
    }
    return AP_ERR_MODEL_FORMAT;
}

ap_status ap_model_load(ap_context *ctx, const char *text, size_t length, ap_model **out, ap_diagnosis *diag)
{
    const char *p = text;
    const char *end = text + length;
    ap_model *m;
    mk_string_list *sys_labels = NULL;
    char **labels = NULL;
    size_t nl = 0;
    size_t width = 0;
    size_t line_no = 0;
    ap_status st = AP_OK;
    char *line;
    int header = 0;

    if (ctx == NULL || text == NULL || out == NULL) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    *out = NULL;
    if (mk_system_vector_width(ctx->system, &width) != MK_OK
        || mk_system_vector_labels(ctx->system, &sys_labels) != MK_OK) {
        return AP_ERR_MERKMAL;
    }
    m = (ap_model *)calloc(1, sizeof(ap_model));
    if (m == NULL) {
        mk_string_list_free(sys_labels);
        return AP_ERR_OOM;
    }
    m->ctx = ctx;
    m->width = width;
    m->g_sub = (double *)calloc(width + 1, sizeof(double));
    m->g_del = (double *)calloc(width + 1, sizeof(double));
    m->w_up = (double *)calloc(width + 1, sizeof(double));
    m->w_down = (double *)calloc(width + 1, sizeof(double));
    m->z_left = (double *)calloc(width + 1, sizeof(double));
    m->z_right = (double *)calloc(width + 1, sizeof(double));
    labels = (char **)calloc(width + 1, sizeof(char *));
    if (m->g_sub == NULL || m->g_del == NULL || m->w_up == NULL || m->w_down == NULL || m->z_left == NULL
        || m->z_right == NULL || labels == NULL) {
        st = AP_ERR_OOM;
    }
    m->vocoid = -1;
    while (st == AP_OK && (line = next_line(&p, end)) != NULL) {
        char *tab = strchr(line, '\t');
        line_no++;
        if (line[0] == '\0' || line[0] == '%') {
            free(line);
            continue;
        }
        if (tab == NULL) {
            st = AP_ERR_MODEL_FORMAT;
        } else {
            *tab = '\0';
            if (!header) {
                header = strcmp(line, AP_MODEL_MAGIC) == 0 && strcmp(tab + 1, "1") == 0;
                if (!header) {
                    st = AP_ERR_MODEL_FORMAT;
                }
            } else if (strcmp(line, "labels") == 0) {
                char *q = tab + 1;
                while (q != NULL && nl <= width) {
                    char *t = strchr(q, '\t');
                    if (t != NULL) {
                        *t = '\0';
                    }
                    if (nl == width) {
                        st = AP_ERR_INCOMPATIBLE;
                        break;
                    }
                    labels[nl] = api_strdup(q);
                    if (strcmp(q, mk_string_list_get(sys_labels, nl)) != 0) {
                        st = AP_ERR_INCOMPATIBLE;
                    }
                    if (strcmp(q, "vocoid") == 0) {
                        m->vocoid = (int)nl;
                    }
                    nl++;
                    q = t != NULL ? t + 1 : NULL;
                }
                if (st == AP_OK && nl != width) {
                    st = AP_ERR_INCOMPATIBLE;
                }
            } else if (strcmp(line, "system") == 0) {
                /* informative; the labels are what is checked */
            } else if (strcmp(line, "param") == 0) {
                char *t = strchr(tab + 1, '\t');
                if (t == NULL || nl != width) {
                    st = AP_ERR_MODEL_FORMAT;
                } else {
                    *t = '\0';
                    st = set_param(m, labels, tab + 1, strtod(t + 1, NULL));
                }
            } else if (strcmp(line, "rule") == 0) {
                char *t = strchr(tab + 1, '\t');
                ap_rule *r = NULL;
                if (t == NULL) {
                    st = AP_ERR_MODEL_FORMAT;
                } else {
                    *t = '\0';
                    /* a rule the engine refuses is skipped, as the fitter's catalogue does */
                    if (ap_rule_parse(ctx, t + 1, &r, NULL) == AP_OK) {
                        ap_rule **rs = (ap_rule **)realloc(m->rules, (m->rule_count + 1) * sizeof(ap_rule *));
                        double *ws = (double *)realloc(m->rule_weight, (m->rule_count + 1) * sizeof(double));
                        if (rs != NULL) {
                            m->rules = rs;
                        }
                        if (ws != NULL) {
                            m->rule_weight = ws;
                        }
                        if (rs == NULL || ws == NULL) {
                            ap_rule_free(r);
                            st = AP_ERR_OOM;
                        } else {
                            m->rules[m->rule_count] = r;
                            m->rule_weight[m->rule_count] = strtod(tab + 1, NULL);
                            m->rule_count++;
                        }
                    }
                }
            } else {
                st = AP_ERR_MODEL_FORMAT;
            }
        }
        free(line);
    }
    if (st == AP_OK && (!header || nl != width || m->vocoid < 0)) {
        st = AP_ERR_MODEL_FORMAT;
    }
    api_free_parts(labels, nl); /* frees the array too, even when empty */
    mk_string_list_free(sys_labels);
    if (st != AP_OK) {
        api_diag(diag, st, line_no, "change model pack, line %zu: %s", line_no, ap_status_string(st));
        ap_model_free(m);
        return st;
    }
    *out = m;
    return AP_OK;
}

/* ---- caches -------------------------------------------------------------- */

static ap_status get_vec(ap_model *m, const char *g, const double **out)
{
    uint32_t i;
    size_t written = 0;

    if (!api_strmap_get(&m->vec_index, g, &i)) {
        double *v;
        if (m->vec_count == m->vec_cap) {
            size_t cap = m->vec_cap == 0 ? 64 : m->vec_cap * 2;
            double *grown = (double *)realloc(m->vecs, cap * m->width * sizeof(double));
            if (grown == NULL) {
                return AP_ERR_OOM;
            }
            m->vecs = grown;
            m->vec_cap = cap;
        }
        v = m->vecs + m->vec_count * m->width;
        if (strcmp(g, "#") == 0 || strcmp(g, "-") == 0
            || mk_system_feature_vector(m->ctx->system, g, v, m->width, &written) != MK_OK) {
            memset(v, 0, m->width * sizeof(double)); /* unknown to merkmal: no features */
        }
        i = (uint32_t)m->vec_count++;
        if (api_strmap_put(&m->vec_index, g, i) != AP_OK) {
            return AP_ERR_OOM;
        }
    }
    *out = m->vecs + (size_t)i * m->width;
    return AP_OK;
}

/* pieces joined with `sep` into buf (capacity checked by the caller) */
static void join3(char *buf, const char *a, const char *b, const char *c, char sep)
{
    size_t la = strlen(a);
    size_t lb = strlen(b);

    memcpy(buf, a, la);
    buf[la] = sep;
    memcpy(buf + la + 1, b, lb);
    if (c != NULL) {
        size_t lc = strlen(c);
        buf[la + 1 + lb] = sep;
        memcpy(buf + la + 2 + lb, c, lc + 1);
    } else {
        buf[la + 1 + lb] = '\0';
    }
}

static ap_status get_dist(ap_model *m, const char *a, const char *b, double *out)
{
    char key[512];
    uint32_t i;

    if (strcmp(a, b) == 0) {
        *out = 0.0;
        return AP_OK;
    }
    if (strlen(a) + strlen(b) + 2 > sizeof(key)) {
        return AP_ERR_LIMIT;
    }
    join3(key, a, b, NULL, '\x1f');
    if (!api_strmap_get(&m->dist_index, key, &i)) {
        double d = 1.0;
        if (m->dist_count == m->dist_cap) {
            size_t cap = m->dist_cap == 0 ? 256 : m->dist_cap * 2;
            double *grown = (double *)realloc(m->dists, cap * sizeof(double));
            if (grown == NULL) {
                return AP_ERR_OOM;
            }
            m->dists = grown;
            m->dist_cap = cap;
        }
        if (mk_system_segment_distance_with_weights(m->ctx->system, a, b, NULL, &d) != MK_OK) {
            d = 1.0; /* not comparable */
        }
        m->dists[m->dist_count] = d;
        i = (uint32_t)m->dist_count++;
        if (api_strmap_put(&m->dist_index, key, i) != AP_OK) {
            return AP_ERR_OOM;
        }
    }
    *out = m->dists[i];
    return AP_OK;
}

static ap_status cat_add(cat_entry *e, const char *y, double w)
{
    size_t j;
    char **rs;
    double *ws;

    for (j = 0; j < e->count; j++) {
        if (strcmp(e->reflex[j], y) == 0) {
            e->weight[j] += w;
            return AP_OK;
        }
    }
    rs = (char **)realloc(e->reflex, (e->count + 1) * sizeof(char *));
    if (rs == NULL) {
        return AP_ERR_OOM;
    }
    e->reflex = rs;
    ws = (double *)realloc(e->weight, (e->count + 1) * sizeof(double));
    if (ws == NULL) {
        return AP_ERR_OOM;
    }
    e->weight = ws;
    e->reflex[e->count] = api_strdup(y);
    if (e->reflex[e->count] == NULL) {
        return AP_ERR_OOM;
    }
    e->weight[e->count] = w;
    e->count++;
    return AP_OK;
}

/* calibrate.Catalogue.reflexes: every catalogue rule applied to "# L s R #";
 * the reflex of s is the element at its position when the length is kept, or
 * deletion when exactly that element is gone */
static ap_status get_cat(ap_model *m, ap_context *ctx, const char *L, const char *s, const char *R, const cat_entry **out)
{
    char key[768];
    uint32_t i;

    if (strlen(L) + strlen(s) + strlen(R) + 3 > sizeof(key)) {
        return AP_ERR_LIMIT;
    }
    join3(key, L, s, R, '\x1f');
    if (!api_strmap_get(&m->cat_index, key, &i)) {
        char text[800];
        ap_seg seq[8];
        ap_seg res[64];
        size_t n = 0;
        size_t r;
        size_t mid = strcmp(L, "#") == 0 ? 1 : 2;
        cat_entry e = { NULL, NULL, 0 };
        ap_status st;

        {   /* "# L s R #", leaving out L and R when they are boundaries */
            size_t w = 0;
            const char *parts[5];
            size_t np = 0;
            size_t k;
            parts[np++] = "#";
            if (strcmp(L, "#") != 0) {
                parts[np++] = L;
            }
            parts[np++] = s;
            if (strcmp(R, "#") != 0) {
                parts[np++] = R;
            }
            parts[np++] = "#";
            for (k = 0; k < np; k++) {
                size_t len = strlen(parts[k]);
                if (k > 0) {
                    text[w++] = ' ';
                }
                memcpy(text + w, parts[k], len);
                w += len;
            }
            text[w] = '\0';
        }
        st = ap_parse_sequence(ctx, text, seq, 8, &n, NULL);
        if (st != AP_OK) {
            return st;
        }
        for (r = 0; r < m->rule_count; r++) {
            size_t w = 0;
            if (ap_forward(ctx, m->rules[r], seq, n, res, 64, &w) != AP_OK) {
                continue;
            }
            if (w == n) {
                const char *y = api_seg(ctx, res[mid])->grapheme;
                if (strcmp(y, s) != 0) {
                    st = cat_add(&e, y, m->rule_weight[r]);
                }
            } else if (w + 1 == n) {
                size_t k;
                int same = 1;
                for (k = 0; k < mid && same; k++) {
                    same = strcmp(api_seg(ctx, res[k])->grapheme, api_seg(ctx, seq[k])->grapheme) == 0;
                }
                for (k = mid; k < w && same; k++) {
                    same = strcmp(api_seg(ctx, res[k])->grapheme, api_seg(ctx, seq[k + 1])->grapheme) == 0;
                }
                if (same) {
                    st = cat_add(&e, "-", m->rule_weight[r]);
                }
            }
            if (st != AP_OK) {
                return st;
            }
        }
        if (m->cat_count == m->cat_cap) {
            size_t cap = m->cat_cap == 0 ? 256 : m->cat_cap * 2;
            cat_entry *grown = (cat_entry *)realloc(m->cats, cap * sizeof(cat_entry));
            if (grown == NULL) {
                return AP_ERR_OOM;
            }
            m->cats = grown;
            m->cat_cap = cap;
        }
        m->cats[m->cat_count] = e;
        i = (uint32_t)m->cat_count++;
        if (api_strmap_put(&m->cat_index, key, i) != AP_OK) {
            return AP_ERR_OOM;
        }
    }
    *out = &m->cats[i];
    return AP_OK;
}

static double cat_weight(const cat_entry *e, const char *y)
{
    size_t j;

    for (j = 0; j < e->count; j++) {
        if (strcmp(e->reflex[j], y) == 0) {
            return e->weight[j];
        }
    }
    return 0.0;
}

/* ---- scoring ------------------------------------------------------------- */

ap_status ap_model_eta(
    ap_model *m, ap_context *ctx, const char *s, const char *L, const char *R,
    const char *const *cands, size_t count, double offset, double *eta)
{
    const double *xs;
    const double *xl;
    const double *xr;
    const cat_entry *cat;
    double base_sub;
    double base_del;
    int env[4];
    size_t c;
    size_t d;
    ap_status st;

    if (m == NULL || ctx == NULL || ctx != m->ctx || s == NULL || L == NULL || R == NULL
        || (cands == NULL && count > 0) || (eta == NULL && count > 0)) {
        return AP_ERR_INVALID_ARGUMENT;
    }
    if ((st = get_vec(m, s, &xs)) != AP_OK) {
        return st;
    }
    if ((st = get_vec(m, L, &xl)) != AP_OK) {
        return st;
    }
    if ((st = get_vec(m, R, &xr)) != AP_OK) {
        return st;
    }
    /* the vector table may have grown: take the pointers after every lookup */
    {
        uint32_t is_;
        uint32_t il;
        uint32_t ir;
        api_strmap_get(&m->vec_index, s, &is_);
        api_strmap_get(&m->vec_index, L, &il);
        api_strmap_get(&m->vec_index, R, &ir);
        xs = m->vecs + (size_t)is_ * m->width;
        xl = m->vecs + (size_t)il * m->width;
        xr = m->vecs + (size_t)ir * m->width;
    }
    if ((st = get_cat(m, ctx, L, s, R, &cat)) != AP_OK) {
        return st;
    }
    env[0] = strcmp(L, "#") == 0;
    env[1] = strcmp(L, "#") != 0 && strcmp(L, "-") != 0 && xl[m->vocoid] > 0;
    env[2] = strcmp(R, "#") == 0;
    env[3] = strcmp(R, "#") != 0 && strcmp(R, "-") != 0 && xr[m->vocoid] > 0;
    base_sub = m->a_sub + offset;
    base_del = m->a_del + offset;
    for (d = 0; d < m->width; d++) {
        base_sub += m->g_sub[d] * xs[d];
        base_del += m->g_del[d] * xs[d];
    }
    for (d = 0; d < 4; d++) {
        if (env[d]) {
            base_sub += m->v_sub[d];
            base_del += m->v_del[d];
        }
    }
    for (c = 0; c < count; c++) {
        const char *y = cands[c];
        if (strcmp(y, s) == 0) {
            eta[c] = 0.0;
        } else if (strcmp(y, "-") == 0) {
            eta[c] = base_del + m->lam * log1p(cat_weight(cat, "-"));
        } else {
            const double *xy;
            double dist = 0.0;
            double e = base_sub;
            uint32_t iy;
            if ((st = get_vec(m, y, &xy)) != AP_OK || (st = get_dist(m, s, y, &dist)) != AP_OK) {
                return st;
            }
            api_strmap_get(&m->vec_index, y, &iy);
            xy = m->vecs + (size_t)iy * m->width;
            {   /* the vector table may have moved: reread s, L, R */
                uint32_t is_;
                uint32_t il;
                uint32_t ir;
                api_strmap_get(&m->vec_index, s, &is_);
                api_strmap_get(&m->vec_index, L, &il);
                api_strmap_get(&m->vec_index, R, &ir);
                xs = m->vecs + (size_t)is_ * m->width;
                xl = m->vecs + (size_t)il * m->width;
                xr = m->vecs + (size_t)ir * m->width;
            }
            e -= m->beta * dist;
            for (d = 0; d < m->width; d++) {
                double diff = xy[d] - xs[d];
                if (fabs(diff) > 1e-9) {
                    e += diff > 0 ? m->w_up[d] : m->w_down[d];
                    if (strcmp(L, "#") != 0 && fabs(xy[d] - xl[d]) < 1e-9) {
                        e += m->z_left[d];
                    }
                    if (strcmp(R, "#") != 0 && fabs(xy[d] - xr[d]) < 1e-9) {
                        e += m->z_right[d];
                    }
                }
            }
            e += m->lam * log1p(cat_weight(cat, y));
            eta[c] = e;
        }
    }
    return AP_OK;
}

ap_status ap_model_logprob(
    ap_model *m, ap_context *ctx, const char *s, const char *L, const char *R,
    const char *const *cands, size_t count, double offset, double *logp)
{
    double mx = -INFINITY;
    double z = 0.0;
    size_t c;
    ap_status st = ap_model_eta(m, ctx, s, L, R, cands, count, offset, logp);

    if (st != AP_OK || count == 0) {
        return st;
    }
    for (c = 0; c < count; c++) {
        if (logp[c] > mx) {
            mx = logp[c];
        }
    }
    for (c = 0; c < count; c++) {
        z += exp(logp[c] - mx);
    }
    z = log(z) + mx;
    for (c = 0; c < count; c++) {
        logp[c] -= z;
    }
    return AP_OK;
}
