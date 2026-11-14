#include "internal.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- labels ------------------------------------------------------------ */

int api_labels_empty(const ap_labels *a)
{
    size_t i;

    for (i = 0; i < AP_LABEL_WORDS; i++) {
        if (a->w[i] != 0) {
            return 0;
        }
    }
    return 1;
}

int api_labels_equal(const ap_labels *a, const ap_labels *b)
{
    return memcmp(a->w, b->w, sizeof(a->w)) == 0;
}

int api_labels_subset(const ap_labels *a, const ap_labels *b)
{
    size_t i;

    for (i = 0; i < AP_LABEL_WORDS; i++) {
        if ((a->w[i] & ~b->w[i]) != 0) {
            return 0;
        }
    }
    return 1;
}

int api_labels_intersect(const ap_labels *a, const ap_labels *b)
{
    size_t i;

    for (i = 0; i < AP_LABEL_WORDS; i++) {
        if ((a->w[i] & b->w[i]) != 0) {
            return 1;
        }
    }
    return 0;
}

int api_labels_has(const ap_labels *a, uint32_t label)
{
    return (int)((a->w[label / 64] >> (label % 64)) & 1u);
}

void api_labels_set(ap_labels *a, uint32_t label)
{
    a->w[label / 64] |= (uint64_t)1 << (label % 64);
}

void api_labels_clear(ap_labels *a, uint32_t label)
{
    a->w[label / 64] &= ~((uint64_t)1 << (label % 64));
}

uint64_t api_hash_bytes(const void *data, size_t len, uint64_t seed)
{
    /* FNV-1a, 64-bit */
    const unsigned char *p = (const unsigned char *)data;
    uint64_t h = 1469598103934665603ULL ^ seed;
    size_t i;

    for (i = 0; i < len; i++) {
        h ^= p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

uint64_t api_labels_hash(const ap_labels *a)
{
    return api_hash_bytes(a->w, sizeof(a->w), 0x9e3779b97f4a7c15ULL);
}

/* ---- strings ------------------------------------------------------------ */

char *api_strndup(const char *s, size_t n)
{
    char *out = (char *)malloc(n + 1);

    if (out == NULL) {
        return NULL;
    }
    memcpy(out, s, n);
    out[n] = '\0';
    return out;
}

char *api_strdup(const char *s)
{
    return api_strndup(s, strlen(s));
}

/* ---- string map --------------------------------------------------------- */

void api_strmap_free(api_strmap *m)
{
    size_t i;

    for (i = 0; i < m->capacity; i++) {
        free(m->keys[i]);
    }
    free(m->keys);
    free(m->values);
    memset(m, 0, sizeof(*m));
}

static size_t strmap_slot(const api_strmap *m, const char *key)
{
    size_t mask = m->capacity - 1;
    size_t i = (size_t)api_hash_bytes(key, strlen(key), 0) & mask;

    while (m->keys[i] != NULL && strcmp(m->keys[i], key) != 0) {
        i = (i + 1) & mask;
    }
    return i;
}

int api_strmap_get(const api_strmap *m, const char *key, uint32_t *value)
{
    size_t i;

    if (m->capacity == 0) {
        return 0;
    }
    i = strmap_slot(m, key);
    if (m->keys[i] == NULL) {
        return 0;
    }
    *value = m->values[i];
    return 1;
}

static ap_status strmap_grow(api_strmap *m)
{
    api_strmap bigger;
    size_t i;

    bigger.capacity = m->capacity == 0 ? 16 : m->capacity * 2;
    bigger.count = m->count;
    bigger.keys = (char **)calloc(bigger.capacity, sizeof(char *));
    bigger.values = (uint32_t *)calloc(bigger.capacity, sizeof(uint32_t));
    if (bigger.keys == NULL || bigger.values == NULL) {
        free(bigger.keys);
        free(bigger.values);
        return AP_ERR_OOM;
    }
    for (i = 0; i < m->capacity; i++) {
        if (m->keys[i] != NULL) {
            size_t j = strmap_slot(&bigger, m->keys[i]);
            bigger.keys[j] = m->keys[i];
            bigger.values[j] = m->values[i];
        }
    }
    free(m->keys);
    free(m->values);
    *m = bigger;
    return AP_OK;
}

ap_status api_strmap_put(api_strmap *m, const char *key, uint32_t value)
{
    size_t i;

    if ((m->count + 1) * 2 > m->capacity) {
        ap_status st = strmap_grow(m);
        if (st != AP_OK) {
            return st;
        }
    }
    i = strmap_slot(m, key);
    if (m->keys[i] == NULL) {
        m->keys[i] = api_strdup(key);
        if (m->keys[i] == NULL) {
            return AP_ERR_OOM;
        }
        m->count++;
    }
    m->values[i] = value;
    return AP_OK;
}

ap_status api_strmap_copy(api_strmap *dst, const api_strmap *src)
{
    size_t i;

    memset(dst, 0, sizeof(*dst));
    if (src->capacity == 0) {
        return AP_OK;
    }
    dst->keys = (char **)calloc(src->capacity, sizeof(char *));
    dst->values = (uint32_t *)malloc(src->capacity * sizeof(uint32_t));
    if (dst->keys == NULL || dst->values == NULL) {
        free(dst->keys);
        free(dst->values);
        memset(dst, 0, sizeof(*dst));
        return AP_ERR_OOM;
    }
    dst->capacity = src->capacity;
    dst->count = src->count;
    memcpy(dst->values, src->values, src->capacity * sizeof(uint32_t));
    for (i = 0; i < src->capacity; i++) {
        if (src->keys[i] != NULL) {
            dst->keys[i] = api_strdup(src->keys[i]);
            if (dst->keys[i] == NULL) {
                api_strmap_free(dst);
                return AP_ERR_OOM;
            }
        }
    }
    return AP_OK;
}

/* ---- segment buffer ----------------------------------------------------- */

ap_status api_segbuf_push(api_segbuf *b, ap_seg s)
{
    if (b->count == b->capacity) {
        size_t cap = b->capacity == 0 ? 16 : b->capacity * 2;
        ap_seg *items = (ap_seg *)realloc(b->items, cap * sizeof(ap_seg));
        if (items == NULL) {
            return AP_ERR_OOM;
        }
        b->items = items;
        b->capacity = cap;
    }
    b->items[b->count++] = s;
    return AP_OK;
}

ap_status api_segbuf_extend(api_segbuf *b, const ap_seg *s, size_t n)
{
    size_t i;

    for (i = 0; i < n; i++) {
        ap_status st = api_segbuf_push(b, s[i]);
        if (st != AP_OK) {
            return st;
        }
    }
    return AP_OK;
}

void api_segbuf_free(api_segbuf *b)
{
    free(b->items);
    memset(b, 0, sizeof(*b));
}

/* ---- text --------------------------------------------------------------- */

size_t api_utf8_decode(const unsigned char *s, size_t len, uint32_t *cp)
{
    /* Malformed bytes decode as themselves, one byte at a time. */
    if (len == 0) {
        *cp = 0;
        return 0;
    }
    if (s[0] < 0x80) {
        *cp = s[0];
        return 1;
    }
    if ((s[0] & 0xE0) == 0xC0 && len >= 2 && (s[1] & 0xC0) == 0x80) {
        *cp = ((uint32_t)(s[0] & 0x1F) << 6) | (uint32_t)(s[1] & 0x3F);
        return 2;
    }
    if ((s[0] & 0xF0) == 0xE0 && len >= 3 && (s[1] & 0xC0) == 0x80 && (s[2] & 0xC0) == 0x80) {
        *cp = ((uint32_t)(s[0] & 0x0F) << 12) | ((uint32_t)(s[1] & 0x3F) << 6)
            | (uint32_t)(s[2] & 0x3F);
        return 3;
    }
    if ((s[0] & 0xF8) == 0xF0 && len >= 4 && (s[1] & 0xC0) == 0x80 && (s[2] & 0xC0) == 0x80
        && (s[3] & 0xC0) == 0x80) {
        *cp = ((uint32_t)(s[0] & 0x07) << 18) | ((uint32_t)(s[1] & 0x3F) << 12)
            | ((uint32_t)(s[2] & 0x3F) << 6) | (uint32_t)(s[3] & 0x3F);
        return 4;
    }
    *cp = 0xFFFFFFFFu; /* a lone byte: never whitespace, never syntax */
    return 1;
}

int api_is_py_space(uint32_t cp)
{
    /* Python's str.isspace() */
    return (cp >= 0x09 && cp <= 0x0D) || (cp >= 0x1C && cp <= 0x20) || cp == 0x85 || cp == 0xA0
        || cp == 0x1680 || (cp >= 0x2000 && cp <= 0x200A) || cp == 0x2028 || cp == 0x2029
        || cp == 0x202F || cp == 0x205F || cp == 0x3000;
}

ap_status api_preprocess(const char *text, char **out)
{
    char *nfd = NULL;
    char *buf;
    size_t len;
    size_t i = 0;
    size_t w = 0;
    int pending_space = 0;
    mk_status ms;
    int ours = 0; /* nfd from malloc, not from merkmal */
    const unsigned char *q = (const unsigned char *)text;

    /* ASCII is its own NFD: skip the normalizer, which allocates */
    while (*q != '\0' && *q < 0x80) {
        q++;
    }
    if (*q == '\0') {
        nfd = (char *)malloc((size_t)(q - (const unsigned char *)text) + 1);
        if (nfd == NULL) {
            return AP_ERR_OOM;
        }
        memcpy(nfd, text, (size_t)(q - (const unsigned char *)text) + 1);
        ours = 1;
        ms = MK_OK;
    } else {
        ms = mk_unicode_normalize(text, MK_NFD, &nfd);
    }
    *out = NULL;
    if (ms == MK_ERR_OOM) {
        return AP_ERR_OOM;
    }
    if (ms != MK_OK) {
        return AP_ERR_MERKMAL;
    }
    len = strlen(nfd);
    buf = (char *)malloc(len + 1);
    if (buf == NULL) {
        if (ours) {
            free(nfd);
        } else {
            mk_string_free(nfd);
        }
        return AP_ERR_OOM;
    }
    while (i < len) {
        uint32_t cp;
        size_t n = api_utf8_decode((const unsigned char *)nfd + i, len - i, &cp);
        if (api_is_py_space(cp)) {
            pending_space = w > 0;
        } else {
            if (pending_space) {
                buf[w++] = ' ';
                pending_space = 0;
            }
            memcpy(buf + w, nfd + i, n);
            w += n;
        }
        i += n;
    }
    buf[w] = '\0';
    if (ours) {
            free(nfd);
        } else {
            mk_string_free(nfd);
        }
    /* "->" to ">" (1.x replaces after collapsing whitespace) */
    {
        size_t r = 0;
        size_t v = 0;
        while (r < w) {
            if (buf[r] == '-' && r + 1 < w && buf[r + 1] == '>') {
                buf[v++] = '>';
                r += 2;
            } else {
                buf[v++] = buf[r++];
            }
        }
        buf[v] = '\0';
    }
    *out = buf;
    return AP_OK;
}

void api_free_parts(char **parts, size_t count)
{
    size_t i;

    if (parts == NULL) {
        return;
    }
    for (i = 0; i < count; i++) {
        free(parts[i]);
    }
    free(parts);
}

ap_status api_split(const char *text, size_t start, size_t end, char ***parts, size_t *count)
{
    /* Python str.split() on preprocessed text: runs of ' ' separate, and
     * leading/trailing spaces give no empty parts. */
    char **items = NULL;
    size_t n = 0;
    size_t cap = 0;
    size_t i = start;

    *parts = NULL;
    *count = 0;
    while (i < end) {
        size_t j;
        while (i < end && text[i] == ' ') {
            i++;
        }
        if (i >= end) {
            break;
        }
        j = i;
        while (j < end && text[j] != ' ') {
            j++;
        }
        if (n == cap) {
            size_t nc = cap == 0 ? 8 : cap * 2;
            char **grown = (char **)realloc(items, nc * sizeof(char *));
            if (grown == NULL) {
                api_free_parts(items, n);
                return AP_ERR_OOM;
            }
            items = grown;
            cap = nc;
        }
        items[n] = api_strndup(text + i, j - i);
        if (items[n] == NULL) {
            api_free_parts(items, n);
            return AP_ERR_OOM;
        }
        n++;
        i = j;
    }
    *parts = items;
    *count = n;
    return AP_OK;
}

/* ---- diagnosis, status, version ----------------------------------------- */

void api_diag(ap_diagnosis *d, ap_status status, size_t offset, const char *fmt, ...)
{
    va_list args;

    if (d == NULL) {
        return;
    }
    d->status = status;
    d->offset = offset;
    va_start(args, fmt);
    vsnprintf(d->message, sizeof(d->message), fmt, args);
    va_end(args);
}

const char *ap_status_string(ap_status status)
{
    switch (status) {
    case AP_OK: return "ok";
    case AP_ERR_INVALID_ARGUMENT: return "invalid argument";
    case AP_ERR_OOM: return "out of memory";
    case AP_ERR_PARSE: return "parse error";
    case AP_ERR_MERKMAL: return "merkmal error";
    case AP_ERR_UNKNOWN_GRAPHEME: return "unknown grapheme";
    case AP_ERR_UNKNOWN_FEATURE: return "unknown feature";
    case AP_ERR_UNKNOWN_CLASS: return "unknown sound class";
    case AP_ERR_LIMIT: return "limit exceeded";
    case AP_ERR_BUFFER_TOO_SMALL: return "buffer too small";
    case AP_ERR_MODEL_FORMAT: return "malformed model";
    case AP_ERR_INCOMPATIBLE: return "incompatible feature system";
    case AP_ERR_RULE: return "rule cannot be applied to this input";
    }
    return "unknown status";
}

const char *ap_version_string(void)
{
    return AP_VERSION_STRING;
}

uint32_t ap_abi_version(void)
{
    return AP_ABI_VERSION;
}

void ap_free(void *pointer)
{
    free(pointer);
}

void ap_strings_free(char **strings, size_t count)
{
    api_free_parts(strings, count);
}
