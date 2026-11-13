/* ap_rule_parse on arbitrary bytes, then the JSON of whatever parsed. */

#include "fuzz_common.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    ap_context *ctx = fuzz_context();
    char *text = fuzz_text(data, size);
    ap_rule *rule = NULL;
    ap_diagnosis diag;

    if (text == NULL) {
        return 0;
    }
    if (ap_rule_parse(ctx, text, &rule, &diag) == AP_OK) {
        char *json = NULL;
        if (ap_rule_to_json(ctx, rule, &json) == AP_OK) {
            ap_free(json);
        }
        ap_rule_free(rule);
    }
    free(text);
    return 0;
}
