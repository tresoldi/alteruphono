/* Forward application. The simultaneous cases are the regression tests of
 * tresoldi/alteruphono#1 (upstream tests/test_simultaneous.py and blindrec's
 * tests/test_alteruphono_simultaneous.py). */

#include "helpers.h"

int main(void)
{
    ap_context *ctx = test_context();

    /* simultaneous (SPE) application: contexts are matched, never consumed */
    CHECK_FWD(ctx, "p > b / V _ V", "# a p a p a #", "# a b a b a #");
    CHECK_FWD(ctx, "S > @1[+voiced] / V _ V", "# k i t a p e k #", "# k i d a b e k #");
    CHECK_FWD(ctx, "{p|t} > {b|d} / V _ V", "# a p a t a #", "# a b a d a #");
    CHECK_FWD(ctx, "t > :null: / t _", "# a t t t a #", "# a t a #");
    CHECK_FWD(ctx, "V s > @1 z @1 / # p|b r _ t|d", "# p r e s t o #", "# p r e z e t o #");

    /* the simple cases */
    CHECK_FWD(ctx, "p > b", "# p a p #", "# b a b #");
    CHECK_FWD(ctx, "C > :null: / _ #", "# a d j a\xcb\x90 d #", "# a d j a\xcb\x90 #");
    CHECK_FWD(ctx, "S > @1[-voiced,+voiceless] / _ #", "# a d #", "# a t #");
    CHECK_FWD(ctx, "N > m / _ #", "# a k u n #", "# a k u m #");
    CHECK_FWD(ctx, "s > h / # _", "# s a s #", "# h a s #");
    CHECK_FWD(ctx, "p > b", "", "");
    CHECK_FWD(ctx, "p > b", "# #", "# #");

    /* quantified rules: simultaneous semantics (fixes Q1 and Q2) */
    CHECK_FWD(ctx, "p > b / V _ V?", "# a p a p a #", "# a b a b a #");
    CHECK_FWD(ctx, "C? p > @1 b / V _", "# a p a p a #", "# a b a b a #");
    CHECK_FWD(ctx, "t > :null: / t+ _", "# a t t t a #", "# a t a #");
    CHECK_FWD(ctx, "C+ > :null: / _ #", "# a s t #", "# a #");
    CHECK_FWD(ctx, "V+ > @1 / _ #", "# p a e i #", "# p i #");

    /* back-references */
    CHECK_FWD(ctx, "p > @0", "# a p a #", "# a p a #");       /* 1.x: @0 is the last element */
    CHECK_FWD(ctx, "p > @9", "# a p a #", "# a a #");         /* out of range: nothing */
    CHECK_FWD(ctx, "t > @1[+bogus]", "# a t a #", "# a t a #"); /* no grapheme: keep it */

    /* sets: an index past the output set is an error, as 1.x's ValueError */
    CHECK_FWD(ctx, "{p|t|k} > {b|d}", "# a k a #", "ERR rule cannot be applied to this input");
    CHECK_FWD(ctx, "{p|t|k} > {b|d}", "# a t a #", "# a d a #");

    /* negation and boundaries */
    CHECK_FWD(ctx, "!V > x / # _", "# t a #", "# x a #");
    CHECK_FWD(ctx, "a > # / _ a", "# a a #", "# # a #");

    /* the buffer contract */
    {
        ap_rule *r = NULL;
        ap_seg in[8];
        ap_seg out[2];
        size_t n = 0;
        size_t w = 0;
        CHECK(ap_rule_parse(ctx, "a > b", &r, NULL) == AP_OK);
        CHECK(ap_parse_sequence(ctx, "# a a #", in, 8, &n, NULL) == AP_OK);
        CHECK(ap_forward(ctx, r, in, n, out, 2, &w) == AP_ERR_BUFFER_TOO_SMALL && w == 4);
        in[1] = 1000000;
        CHECK(ap_forward(ctx, r, in, n, out, 2, &w) == AP_ERR_INVALID_ARGUMENT);
        ap_rule_free(r);
    }

    ap_context_free(ctx);
    return test_finish("forward");
}
