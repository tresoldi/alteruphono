/* Context, segments and the alteruphono-1 projection (docs/v2/DESIGN.md 4.1). */

#include "helpers.h"

static int has_label(ap_context *ctx, ap_seg s, const char *label)
{
    char **labels = NULL;
    size_t n = 0;
    size_t i;
    int found = 0;

    if (ap_seg_labels(ctx, s, &labels, &n) != AP_OK) {
        return -1;
    }
    for (i = 0; i < n; i++) {
        if (strcmp(labels[i], label) == 0) {
            found = 1;
        }
    }
    ap_strings_free(labels, n);
    return found;
}

int main(void)
{
    ap_context *ctx = test_context();
    ap_context *clone = NULL;
    ap_seg p;
    ap_seg p2;
    ap_seg v;
    ap_seg unknown;
    ap_seg ts;
    ap_seg tone;
    const char *g = NULL;
    int partial = -1;
    int found = -1;
    char **labels = NULL;
    size_t n = 0;

    CHECK(ap_abi_version() == AP_ABI_VERSION);
    CHECK(strcmp(ap_version_string(), AP_VERSION_STRING) == 0);
    CHECK(strcmp(ap_status_string(AP_OK), "ok") == 0);
    CHECK(strcmp(ap_status_string((ap_status)999), "unknown status") == 0);

    /* labels come from merkmal, restricted to the 1.x vocabulary */
    CHECK(ap_intern(ctx, "p", &p) == AP_OK);
    CHECK(ap_seg_labels(ctx, p, &labels, &n) == AP_OK);
    CHECK(n == 4);
    if (n == 4) {
        CHECK(strcmp(labels[0], "bilabial") == 0);
        CHECK(strcmp(labels[1], "consonant") == 0);
        CHECK(strcmp(labels[2], "stop") == 0);
        CHECK(strcmp(labels[3], "voiceless") == 0);
    }
    ap_strings_free(labels, n);
    CHECK(has_label(ctx, p, "labial") == 0); /* dropped by the projection */

    /* interning: same grapheme, same id */
    CHECK(ap_intern(ctx, "p", &p2) == AP_OK && p2 == p);
    CHECK(ap_intern(ctx, "#", &p2) == AP_OK && p2 != AP_SEG_BOUNDARY); /* 1.x: Sound("#") */
    {
        const char *const lab[] = { "voiced", "x-new-label" };
        ap_seg h;
        int f = -1;
        CHECK(ap_intern_labels(ctx, "q", lab, 2, 0, &h) == AP_OK);
        CHECK(has_label(ctx, h, "x-new-label") == 1);
        CHECK(ap_class_features(ctx, "R", &labels, &n, &f) == AP_OK && f == 1 && n == 2);
        if (n == 2) {
            CHECK(strcmp(labels[0], "-stop") == 0 && strcmp(labels[1], "consonant") == 0);
        }
        ap_strings_free(labels, n);
        CHECK(ap_class_features(ctx, "p", &labels, &n, &f) == AP_OK && f == 0);
    }

    /* a class is a partial segment with the class's features */
    CHECK(ap_intern(ctx, "V", &v) == AP_OK);
    CHECK(ap_seg_is_partial(ctx, v, &partial) == AP_OK && partial == 1);
    CHECK(has_label(ctx, v, "vowel") == 1);

    /* an unknown grapheme keeps its text and has no features, as in 1.x */
    CHECK(ap_intern(ctx, "qq\xcc\x83", &unknown) == AP_OK);
    CHECK(ap_seg_labels(ctx, unknown, &labels, &n) == AP_OK && n == 0);
    ap_strings_free(labels, n);

    /* D1 cases: merkmal's values win */
    CHECK(ap_intern(ctx, "\xca\x88\xca\x82\xcb\x90", &ts) == AP_OK);   /* ʈʂː */
    CHECK(has_label(ctx, ts, "voiceless") == 1);
    CHECK(has_label(ctx, ts, "voiced") == 0);
    CHECK(ap_intern(ctx, "a\xcc\x82", &tone) == AP_OK);               /* â, NFD */
    CHECK(has_label(ctx, tone, "with_falling_tone") == 1);

    /* 1.x lookup is exact over its grapheme universe: ASCII g is a key, ɡ is not */
    CHECK(ap_grapheme_features(ctx, "g", &labels, &n, &found) == AP_OK && found == 1);
    ap_strings_free(labels, n);
    CHECK(ap_grapheme_features(ctx, "\xc9\xa1", &labels, &n, &found) == AP_OK && found == 0);

    /* reverse lookup, first match in 1.x file order */
    {
        const char *const b_labels[] = { "bilabial", "consonant", "stop", "voiced" };
        const char *const none[] = { "bilabial", "nonsense-label" };
        CHECK(ap_features_grapheme(ctx, b_labels, 4, &g, &found) == AP_OK && found == 1);
        CHECK(found == 1 && strcmp(g, "b") == 0);
        CHECK(ap_features_grapheme(ctx, none, 2, &g, &found) == AP_OK && found == 0);
    }

    /* a clone answers the same, and is independent */
    CHECK(ap_context_clone(ctx, &clone) == AP_OK);
    CHECK(ap_seg_grapheme(clone, p, &g) == AP_OK && strcmp(g, "p") == 0);
    CHECK(ap_intern(clone, "p", &p2) == AP_OK && p2 == p);
    CHECK(ap_intern(clone, "zz", &p2) == AP_OK);
    CHECK(ap_seg_grapheme(ctx, p2, &g) == AP_ERR_INVALID_ARGUMENT); /* not in the original */
    ap_context_free(clone);

    /* argument checks */
    CHECK(ap_context_new(NULL, NULL, &clone, NULL) == AP_ERR_INVALID_ARGUMENT);
    CHECK(ap_intern(NULL, "p", &p2) == AP_ERR_INVALID_ARGUMENT);
    CHECK(ap_seg_grapheme(ctx, 999999, &g) == AP_ERR_INVALID_ARGUMENT);
    {
        ap_context_options o;
        ap_diagnosis d;
        const mk_system *sys = NULL;
        ap_context_options_init_defaults(&o);
        o.projection = AP_PROJECTION_NATIVE;
        mk_registry_get_system(test_registry, "descriptive", &sys);
        memset(&d, 0, sizeof(d));
        CHECK(ap_context_new(sys, &o, &clone, &d) == AP_ERR_INVALID_ARGUMENT);
        CHECK(clone == NULL && d.status == AP_ERR_INVALID_ARGUMENT);
    }

    ap_context_free(ctx);
    return test_finish("context");
}
