/* ap_model_load on arbitrary bytes, then one scoring call on whatever loaded. */

#include "fuzz_common.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    ap_context *ctx = fuzz_context();
    ap_model *m = NULL;
    static const char *const cands[3] = { "p", "b", "-" };
    double eta[3];

    if (ap_model_load(ctx, (const char *)data, size, &m, NULL) == AP_OK) {
        ap_model_eta(m, ctx, "p", "a", "#", cands, 3, 0.0, eta);
        ap_model_free(m);
    }
    return 0;
}
