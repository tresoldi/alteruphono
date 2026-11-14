#ifndef AP_FUZZ_COMMON_H
#define AP_FUZZ_COMMON_H

/* One merkmal registry per process, and one alteruphono context rebuilt every
 * FUZZ_CONTEXT_REUSE inputs: building them is the expensive part, and a
 * context grows with every segment an input interns (by design: segments are
 * interned per context), so a context kept forever would only measure that
 * growth. Reuse across inputs is itself part of what is fuzzed. */
#define FUZZ_CONTEXT_REUSE 2000

#include "alteruphono.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static ap_context *fuzz_context(void)
{
    static mk_registry *reg = NULL;
    static ap_context *ctx = NULL;
    static unsigned uses = 0;
    const mk_system *sys = NULL;

    if (ctx != NULL && ++uses >= FUZZ_CONTEXT_REUSE) {
        ap_context_free(ctx);
        ctx = NULL;
        uses = 0;
    }
    if (reg == NULL && mk_registry_new_builtin(&reg) != MK_OK) {
        abort();
    }
    if (ctx == NULL) {
        if (mk_registry_get_system(reg, "descriptive", &sys) != MK_OK
            || ap_context_new(sys, NULL, &ctx, NULL) != AP_OK) {
            abort();
        }
    }
    return ctx;
}

/* A NUL-terminated copy of the input, or NULL. */
static char *fuzz_text(const uint8_t *data, size_t size)
{
    char *s = (char *)malloc(size + 1);

    if (s != NULL) {
        memcpy(s, data, size);
        s[size] = '\0';
    }
    return s;
}

#endif
