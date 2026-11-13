/* A rule and a sequence, split at the first newline: parse both, then
 * forward and backward (backward under a small candidate cap). */

#include "fuzz_common.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    ap_context *ctx = fuzz_context();
    char *text = fuzz_text(data, size);
    char *nl;
    ap_rule *rule = NULL;
    ap_seg in[48];
    ap_seg out[512];
    size_t n = 0;
    size_t w = 0;

    if (text == NULL) {
        return 0;
    }
    nl = strchr(text, '\n');
    if (nl != NULL) {
        *nl = '\0';
        if (ap_rule_parse(ctx, text, &rule, NULL) == AP_OK
            && ap_parse_sequence(ctx, nl + 1, in, 48, &n, NULL) == AP_OK) {
            ap_candidates *c = NULL;
            ap_forward(ctx, rule, in, n, out, 512, &w);
            if (n <= 12 && ap_backward(ctx, rule, in, n, &c) == AP_OK) {
                ap_candidates_free(c);
            }
        }
        ap_rule_free(rule);
    }
    free(text);
    return 0;
}
