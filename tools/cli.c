/* Line-oriented driver for the parity harness (tests/parity/).
 *
 * Reads lines "F\t<rule>\t<sequence>" or "B\t<rule>\t<sequence>" from stdin
 * and writes one line per input:
 *   OK\t<seq>            forward: the output sequence
 *   OK\t<seq>\x1d<seq>…  backward: the candidates
 *   ERR\t<status>        the rule or input was refused
 * A sequence is its elements joined by \x1f; an element is
 * grapheme \x1e sorted labels joined by "," \x1e partial (0/1); a boundary is
 * "#\x1e\x1e0". The Python oracle writes the same format. */

#include "alteruphono.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void put_seq(const ap_context *ctx, const ap_seg *seq, size_t n)
{
    size_t i;

    for (i = 0; i < n; i++) {
        const char *g = NULL;
        char **labels = NULL;
        size_t count = 0;
        size_t j;
        int partial = 0;
        if (i > 0) {
            fputc('\x1f', stdout);
        }
        if (seq[i] == AP_SEG_BOUNDARY) {
            fputs("#\x1e\x1e" "0", stdout);
            continue;
        }
        ap_seg_grapheme(ctx, seq[i], &g);
        ap_seg_labels(ctx, seq[i], &labels, &count);
        ap_seg_is_partial(ctx, seq[i], &partial);
        fputs(g, stdout);
        fputc('\x1e', stdout);
        for (j = 0; j < count; j++) {
            if (j > 0) {
                fputc(',', stdout);
            }
            fputs(labels[j], stdout);
        }
        fputc('\x1e', stdout);
        fputc(partial ? '1' : '0', stdout);
        ap_strings_free(labels, count);
    }
}

int main(int argc, char **argv)
{
    mk_registry *reg = NULL;
    const mk_system *sys = NULL;
    ap_context *ctx = NULL;
    char *line = NULL;
    size_t cap = 0;
    size_t buf_cap = 4096;
    ap_seg *in = (ap_seg *)malloc(buf_cap * sizeof(ap_seg));
    ap_seg *out = (ap_seg *)malloc(buf_cap * sizeof(ap_seg));
    const char *system = argc > 1 ? argv[1] : "descriptive";

    if (in == NULL || out == NULL || mk_registry_new_builtin(&reg) != MK_OK
        || mk_registry_get_system(reg, system, &sys) != MK_OK
        || ap_context_new(sys, NULL, &ctx, NULL) != AP_OK) {
        fprintf(stderr, "cannot set up\n");
        return 2;
    }
    for (;;) {
        size_t len = 0;
        int c;
        char *rule_text;
        char *seq_text;
        char *tab;
        ap_rule *rule = NULL;
        size_t n = 0;
        size_t written = 0;
        ap_status st;

        while ((c = getchar()) != EOF && c != '\n') {
            if (len + 2 > cap) {
                cap = cap == 0 ? 1024 : cap * 2;
                line = (char *)realloc(line, cap);
                if (line == NULL) {
                    return 2;
                }
            }
            line[len++] = (char)c;
        }
        if (c == EOF && len == 0) {
            break;
        }
        line[len] = '\0';
        if (len < 2 || line[1] != '\t' || (tab = strchr(line + 2, '\t')) == NULL) {
            printf("ERR\tbad-line\n");
            continue;
        }
        *tab = '\0';
        rule_text = line + 2;
        seq_text = tab + 1;
        st = ap_rule_parse(ctx, rule_text, &rule, NULL);
        if (st == AP_OK) {
            st = ap_parse_sequence(ctx, seq_text, in, buf_cap, &n, NULL);
        }
        if (st == AP_OK && line[0] == 'F') {
            st = ap_forward(ctx, rule, in, n, out, buf_cap, &written);
            if (st == AP_OK) {
                fputs("OK\t", stdout);
                put_seq(ctx, out, written);
                fputc('\n', stdout);
            }
        } else if (st == AP_OK && line[0] == 'B') {
            ap_candidates *cands = NULL;
            st = ap_backward(ctx, rule, in, n, &cands);
            if (st == AP_OK) {
                size_t i;
                fputs("OK\t", stdout);
                for (i = 0; i < ap_candidates_count(cands); i++) {
                    const ap_seg *s;
                    size_t sl;
                    if (i > 0) {
                        fputc('\x1d', stdout);
                    }
                    ap_candidates_get(cands, i, &s, &sl);
                    put_seq(ctx, s, sl);
                }
                fputc('\n', stdout);
            }
            ap_candidates_free(cands);
        }
        if (st != AP_OK) {
            printf("ERR\t%s\n", ap_status_string(st));
        }
        ap_rule_free(rule);
        fflush(stdout);
    }
    free(line);
    free(in);
    free(out);
    ap_context_free(ctx);
    mk_registry_free(reg);
    return 0;
}
