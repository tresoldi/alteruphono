/* Every rule of resources/sound_changes.tsv must turn its TEST_ANTE into its
 * TEST_POST (both wrapped in "# ... #", as the catalogue's boundary rules
 * need; compared in NFD). */

#include "helpers.h"

static char *nfd(const char *s)
{
    char *out = NULL;

    if (mk_unicode_normalize(s, MK_NFD, &out) != MK_OK) {
        return NULL;
    }
    return out;
}

int main(void)
{
    ap_context *ctx = test_context();
    char path[4096];
    FILE *f;
    char line[8192];
    size_t rules = 0;
    size_t passed = 0;

    snprintf(path, sizeof(path), "%s/resources/sound_changes.tsv", AP_SOURCE_DIR);
    f = fopen(path, "r");
    if (f == NULL) {
        fprintf(stderr, "cannot open %s\n", path);
        return 2;
    }
    if (fgets(line, sizeof(line), f) == NULL) { /* header */
        fclose(f);
        return 2;
    }
    while (fgets(line, sizeof(line), f) != NULL) {
        char *fields[5];
        char *p = line;
        size_t k;
        char ante[2048];
        char post[2048];
        char *got;
        char *a;
        char *b;

        line[strcspn(line, "\r\n")] = '\0';
        for (k = 0; k < 5; k++) {
            fields[k] = p;
            p = strchr(p, '\t');
            if (p == NULL && k < 4) {
                break;
            }
            if (p != NULL) {
                *p++ = '\0';
            }
        }
        if (k < 4) {
            continue;
        }
        rules++;
        snprintf(ante, sizeof(ante), "# %s #", fields[3]);
        snprintf(post, sizeof(post), "# %s #", fields[4]);
        got = fwd_text(ctx, fields[1], ante);
        a = got != NULL ? nfd(got) : NULL;
        b = nfd(post);
        if (a != NULL && b != NULL && strcmp(a, b) == 0) {
            passed++;
        } else {
            fprintf(stderr, "rule %s (%s): %s -> got \"%s\", expected \"%s\"\n",
                fields[0], fields[1], ante, got ? got : "(null)", post);
            failures++;
        }
        mk_string_free(a);
        mk_string_free(b);
        free(got);
    }
    fclose(f);
    CHECK(rules == 801);
    printf("catalogue: %zu of %zu test pairs\n", passed, rules);
    ap_context_free(ctx);
    return test_finish("catalogue");
}
