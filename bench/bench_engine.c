/* C-level speed of the engine on the catalogue stream: every rule of
 * resources/sound_changes.tsv is parsed, and 20,000 (rule, word) pairs drawn
 * with a fixed seed from the catalogue's rules and its TEST_ANTE words are
 * applied. The same stream as bench/bench_python.py, so the two compare.
 *
 *   bench_engine <repo root> [pairs]
 */

#include "alteruphono.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* CPU time: C99 has no wall clock; the benchmark is single-threaded. */
static double now(void)
{
    return (double)clock() / (double)CLOCKS_PER_SEC;
}

static uint64_t rng_state = 20261113u;

static uint32_t next_u32(void)
{
    /* splitmix64 */
    uint64_t z = (rng_state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return (uint32_t)((z ^ (z >> 31)) >> 32);
}

int main(int argc, char **argv)
{
    char path[4096];
    char line[8192];
    FILE *f;
    char **rules_text = NULL;
    char **words_text = NULL;
    size_t nr = 0;
    size_t i;
    size_t pairs = argc > 2 ? (size_t)strtoul(argv[2], NULL, 10) : 20000;
    mk_registry *reg = NULL;
    const mk_system *sys = NULL;
    ap_context *ctx = NULL;
    ap_rule **rules;
    ap_seg (*words)[64];
    size_t *wlen;
    size_t *pr;
    size_t *pw;
    ap_seg out[256];
    size_t w = 0;
    size_t total_len = 0;
    double t0;
    double t_parse;
    double t_seq;
    double t_fwd;
    double t_bwd;
    size_t nb;

    if (argc < 2) {
        fprintf(stderr, "usage: bench_engine <repo root> [pairs]\n");
        return 2;
    }
    snprintf(path, sizeof(path), "%s/resources/sound_changes.tsv", argv[1]);
    f = fopen(path, "r");
    if (f == NULL || fgets(line, sizeof(line), f) == NULL) {
        return 2;
    }
    rules_text = (char **)calloc(2048, sizeof(char *));
    words_text = (char **)calloc(2048, sizeof(char *));
    while (nr < 2048 && fgets(line, sizeof(line), f) != NULL) {
        char *fields[5];
        char *p = line;
        size_t k;
        line[strcspn(line, "\r\n")] = '\0';
        for (k = 0; k < 5 && p != NULL; k++) {
            fields[k] = p;
            p = strchr(p, '\t');
            if (p != NULL) {
                *p++ = '\0';
            }
        }
        if (k < 5) {
            continue;
        }
        rules_text[nr] = (char *)malloc(strlen(fields[1]) + 1);
        strcpy(rules_text[nr], fields[1]);
        words_text[nr] = (char *)malloc(strlen(fields[3]) + 8);
        sprintf(words_text[nr], "# %s #", fields[3]);
        nr++;
    }
    fclose(f);

    if (mk_registry_new_builtin(&reg) != MK_OK || mk_registry_get_system(reg, "descriptive", &sys) != MK_OK
        || ap_context_new(sys, NULL, &ctx, NULL) != AP_OK) {
        return 2;
    }
    rules = (ap_rule **)calloc(nr, sizeof(ap_rule *));
    words = (ap_seg(*)[64])calloc(nr, sizeof(*words));
    wlen = (size_t *)calloc(nr, sizeof(size_t));
    pr = (size_t *)malloc(pairs * sizeof(size_t));
    pw = (size_t *)malloc(pairs * sizeof(size_t));

    /* warm the context: the first parse resolves every grapheme once */
    for (i = 0; i < nr; i++) {
        ap_rule *r = NULL;
        ap_rule_parse(ctx, rules_text[i], &r, NULL);
        ap_rule_free(r);
        ap_parse_sequence(ctx, words_text[i], words[i], 64, &wlen[i], NULL);
    }
    t0 = now();
    for (i = 0; i < nr; i++) {
        if (ap_rule_parse(ctx, rules_text[i], &rules[i], NULL) != AP_OK) {
            return 3;
        }
    }
    t_parse = (now() - t0) / (double)nr;
    t0 = now();
    for (i = 0; i < nr; i++) {
        ap_parse_sequence(ctx, words_text[i], words[i], 64, &wlen[i], NULL);
    }
    t_seq = (now() - t0) / (double)nr;
    for (i = 0; i < pairs; i++) {
        pr[i] = next_u32() % nr;
        pw[i] = next_u32() % nr;
        total_len += wlen[pw[i]];
    }
    /* untimed pass: modifier outputs intern their segments once */
    for (i = 0; i < pairs; i++) {
        ap_forward(ctx, rules[pr[i]], words[pw[i]], wlen[pw[i]], out, 256, &w);
    }
    t0 = now();
    for (i = 0; i < pairs; i++) {
        ap_forward(ctx, rules[pr[i]], words[pw[i]], wlen[pw[i]], out, 256, &w);
    }
    t_fwd = (now() - t0) / (double)pairs;
    nb = pairs / 10;
    t0 = now();
    for (i = 0; i < nb; i++) {
        ap_candidates *c = NULL;
        if (ap_backward(ctx, rules[pr[i]], words[pw[i]], wlen[pw[i]], &c) == AP_OK) {
            ap_candidates_free(c);
        }
    }
    t_bwd = (now() - t0) / (double)nb;
    printf("{\"engine\": \"c\", \"rules\": %zu, \"pairs\": %zu, \"mean_word_len\": %.2f, "
           "\"parse_rule_us\": %.3f, \"parse_sequence_us\": %.3f, \"forward_us\": %.4f, \"backward_us\": %.3f}\n",
        nr, pairs, (double)total_len / (double)pairs, t_parse * 1e6, t_seq * 1e6, t_fwd * 1e6, t_bwd * 1e6);
    for (i = 0; i < nr; i++) {
        ap_rule_free(rules[i]);
        free(rules_text[i]);
        free(words_text[i]);
    }
    free(rules);
    free(rules_text);
    free(words_text);
    free(words);
    free(wlen);
    free(pr);
    free(pw);
    ap_context_free(ctx);
    mk_registry_free(reg);
    return 0;
}
