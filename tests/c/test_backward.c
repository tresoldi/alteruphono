/* Backward reconstruction, as 1.x with tresoldi/alteruphono 3fdb52b. */

#include "helpers.h"

int main(void)
{
    ap_context *ctx = test_context();

    CHECK_BWD(ctx, "p > b / V _ V", "# a b a #", "# a b a # || # a p a #");
    /* 3fdb52b: every alternative of an unresolved choice is restored */
    CHECK_BWD(ctx, "x|h > :null: / a _ k", "# a k #", "# a h k # || # a k # || # a x k #");
    /* 1.x inverts "+voiced" to "-voiced", which removes voicing without
     * adding voicelessness: the "undone" d keeps its grapheme, and the
     * duplicate is dropped. A known weakness of 1.x, reproduced. */
    CHECK_BWD(ctx, "S > @1[+voiced] / V _ V", "# a d a #", "# a d a #");
    /* with both sides written out, the inversion works */
    CHECK_BWD(ctx, "S > @1[-voiced,+voiceless] / _ #", "# a t #", "# a d # || # a t #");
    CHECK_BWD(ctx, "{p|t} > {b|d} / V _ V", "# a d a #", "# a d a # || # a t a #");
    CHECK_BWD(ctx, "p > b", "", "");
    /* a back-reference out of range is 1.x's IndexError */
    CHECK_BWD(ctx, "p > @9", "# a p a #", "ERR rule cannot be applied to this input");
    /* an exponential product is refused rather than built */
    {
        ap_context_options o;
        ap_context *small = NULL;
        const mk_system *sys = NULL;
        ap_context_options_init_defaults(&o);
        o.max_backward_candidates = 8;
        mk_registry_get_system(test_registry, "descriptive", &sys);
        CHECK(ap_context_new(sys, &o, &small, NULL) == AP_OK);
        CHECK_BWD(small, "a > b", "# b b b b #", "ERR limit exceeded"); /* 16 > 8 */
        CHECK_BWD(small, "a > b", "# b b b #",
            "# a a a # || # a a b # || # a b a # || # a b b # || # b a a # || # b a b # || # b b a # || # b b b #");
        CHECK_BWD(small, "a > b", "# b b #", "# a a # || # a b # || # b a # || # b b #");
        ap_context_free(small);
    }

    ap_context_free(ctx);
    return test_finish("backward");
}
