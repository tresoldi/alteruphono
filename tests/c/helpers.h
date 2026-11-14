#ifndef AP_TEST_HELPERS_H
#define AP_TEST_HELPERS_H

/* Shared by the C tests: a context on merkmal's `descriptive` system, and
 * forward/backward on text. Every helper is static: each test is one file. */

#include "alteruphono.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(__GNUC__) || defined(__clang__)
#define AP_TEST_UNUSED __attribute__((unused))
#else
#define AP_TEST_UNUSED
#endif

static int failures = 0;

#define CHECK(cond) \
    do { \
        if (!(cond)) { \
            fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #cond); \
            failures++; \
        } \
    } while (0)

static mk_registry *test_registry = NULL;

static AP_TEST_UNUSED ap_context *test_context(void)
{
    const mk_system *sys = NULL;
    ap_context *ctx = NULL;

    if (test_registry == NULL && mk_registry_new_builtin(&test_registry) != MK_OK) {
        fprintf(stderr, "no merkmal registry\n");
        exit(2);
    }
    if (mk_registry_get_system(test_registry, "descriptive", &sys) != MK_OK
        || ap_context_new(sys, NULL, &ctx, NULL) != AP_OK) {
        fprintf(stderr, "no context\n");
        exit(2);
    }
    return ctx;
}

static AP_TEST_UNUSED void test_teardown(void)
{
    mk_registry_free(test_registry);
    test_registry = NULL;
}

/* forward(rule, seq) as rendered text, or "ERR <status>"; owned */
static AP_TEST_UNUSED char *fwd_text(ap_context *ctx, const char *rule_text, const char *seq_text)
{
    ap_rule *rule = NULL;
    ap_seg in[256];
    ap_seg out[512];
    size_t n = 0;
    size_t w = 0;
    char *res = NULL;
    ap_status st = ap_rule_parse(ctx, rule_text, &rule, NULL);

    if (st == AP_OK) {
        st = ap_parse_sequence(ctx, seq_text, in, 256, &n, NULL);
    }
    if (st == AP_OK) {
        st = ap_forward(ctx, rule, in, n, out, 512, &w);
    }
    if (st == AP_OK) {
        st = ap_render_sequence(ctx, out, w, &res);
    }
    ap_rule_free(rule);
    if (st != AP_OK) {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR %s", ap_status_string(st));
        res = (char *)malloc(strlen(buf) + 1);
        if (res != NULL) {
            memcpy(res, buf, strlen(buf) + 1);
        }
    }
    return res;
}

static AP_TEST_UNUSED void check_fwd(ap_context *ctx, const char *rule, const char *seq, const char *expected,
                      const char *file, int line)
{
    char *got = fwd_text(ctx, rule, seq);

    if (got == NULL || strcmp(got, expected) != 0) {
        fprintf(stderr, "%s:%d: forward(%s, %s): got \"%s\", expected \"%s\"\n",
            file, line, rule, seq, got == NULL ? "(null)" : got, expected);
        failures++;
    }
    free(got);
}

#define CHECK_FWD(ctx, rule, seq, expected) check_fwd(ctx, rule, seq, expected, __FILE__, __LINE__)

/* backward candidates joined by " || "; owned */
static AP_TEST_UNUSED char *bwd_text(ap_context *ctx, const char *rule_text, const char *seq_text)
{
    ap_rule *rule = NULL;
    ap_candidates *c = NULL;
    ap_seg in[256];
    size_t n = 0;
    size_t i;
    size_t len = 1;
    char *res = NULL;
    ap_status st = ap_rule_parse(ctx, rule_text, &rule, NULL);

    if (st == AP_OK) {
        st = ap_parse_sequence(ctx, seq_text, in, 256, &n, NULL);
    }
    if (st == AP_OK) {
        st = ap_backward(ctx, rule, in, n, &c);
    }
    if (st == AP_OK) {
        res = (char *)calloc(1, 1);
        for (i = 0; res != NULL && i < ap_candidates_count(c); i++) {
            const ap_seg *s;
            size_t sl;
            char *one = NULL;
            char *grown;
            ap_candidates_get(c, i, &s, &sl);
            ap_render_sequence(ctx, s, sl, &one);
            len += strlen(one) + 4;
            grown = (char *)realloc(res, len);
            if (grown == NULL) {
                free(res);
                res = NULL;
            } else {
                res = grown;
                if (i > 0) {
                    strcat(res, " || ");
                }
                strcat(res, one);
            }
            ap_free(one);
        }
    }
    ap_candidates_free(c);
    ap_rule_free(rule);
    if (st != AP_OK) {
        char buf[128];
        snprintf(buf, sizeof(buf), "ERR %s", ap_status_string(st));
        res = (char *)malloc(strlen(buf) + 1);
        if (res != NULL) {
            memcpy(res, buf, strlen(buf) + 1);
        }
    }
    return res;
}

static AP_TEST_UNUSED void check_bwd(ap_context *ctx, const char *rule, const char *seq, const char *expected,
                      const char *file, int line)
{
    char *got = bwd_text(ctx, rule, seq);

    if (got == NULL || strcmp(got, expected) != 0) {
        fprintf(stderr, "%s:%d: backward(%s, %s): got \"%s\", expected \"%s\"\n",
            file, line, rule, seq, got == NULL ? "(null)" : got, expected);
        failures++;
    }
    free(got);
}

#define CHECK_BWD(ctx, rule, seq, expected) check_bwd(ctx, rule, seq, expected, __FILE__, __LINE__)

static AP_TEST_UNUSED int test_finish(const char *name)
{
    test_teardown();
    if (failures != 0) {
        fprintf(stderr, "%s: %d failure(s)\n", name, failures);
        return 1;
    }
    return 0;
}

#endif
