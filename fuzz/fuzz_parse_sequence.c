/* ap_parse_sequence and ap_render_sequence on arbitrary bytes. */

#include "fuzz_common.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    ap_context *ctx = fuzz_context();
    char *text = fuzz_text(data, size);
    ap_seg buf[64];
    size_t n = 0;

    if (text == NULL) {
        return 0;
    }
    if (ap_parse_sequence(ctx, text, buf, 64, &n, NULL) == AP_OK) {
        char *out = NULL;
        if (ap_render_sequence(ctx, buf, n, &out) == AP_OK) {
            ap_free(out);
        }
    }
    free(text);
    return 0;
}
