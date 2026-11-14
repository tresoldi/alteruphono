/* The rule notation, as alteruphono 1.x parser.py accepts it. */

#include "helpers.h"

static ap_status parse(ap_context *ctx, const char *text)
{
    ap_rule *r = NULL;
    ap_diagnosis d;
    ap_status st;

    memset(&d, 0, sizeof(d));
    st = ap_rule_parse(ctx, text, &r, &d);
    if (st == AP_OK) {
        CHECK(r != NULL);
    } else {
        CHECK(r == NULL);
        CHECK(d.status == st);
        CHECK(d.message[0] != '\0');
    }
    ap_rule_free(r);
    return st;
}

static void check_json(ap_context *ctx, const char *text, const char *expected)
{
    ap_rule *r = NULL;
    char *json = NULL;

    CHECK(ap_rule_parse(ctx, text, &r, NULL) == AP_OK);
    CHECK(ap_rule_to_json(ctx, r, &json) == AP_OK);
    if (json != NULL) {
        /* segment ids depend on interning order: mask them as "@" */
        char *rd = json;
        char *wr = json;
        while (*rd != '\0') {
            if (strncmp(rd, "\"id\":", 5) == 0) {
                rd += 5;
                while (*rd >= '0' && *rd <= '9') {
                    rd++; /* skip first: the write below may overlap */
                }
                memcpy(wr, "\"id\":@", 6);
                wr += 6;
            } else {
                *wr++ = *rd++;
            }
        }
        *wr = '\0';
    }
    if (json == NULL || strcmp(json, expected) != 0) {
        fprintf(stderr, "json for %s:\n  got      %s\n  expected %s\n", text, json ? json : "(null)", expected);
        failures++;
    }
    ap_free(json);
    ap_rule_free(r);
}

int main(void)
{
    ap_context *ctx = test_context();
    ap_seg buf[8];
    size_t n = 0;

    /* accepted forms */
    CHECK(parse(ctx, "p > b") == AP_OK);
    CHECK(parse(ctx, "p>b") == AP_OK);
    CHECK(parse(ctx, "p -> b") == AP_OK);
    CHECK(parse(ctx, "p \xe2\x86\x92 b") == AP_OK);          /* → */
    CHECK(parse(ctx, "  p\t>\n b  /  V _ V ") == AP_OK);
    CHECK(parse(ctx, "V s > @1 z @1 / # p|b r _ t|d") == AP_OK);
    CHECK(parse(ctx, "{p|t} > {b|d} / V _ V") == AP_OK);
    CHECK(parse(ctx, "S > @1[+voiced,-voiceless] / _ #") == AP_OK);
    CHECK(parse(ctx, "C+ > :null: / _ #") == AP_OK);
    CHECK(parse(ctx, "_.onset p > b") == AP_OK);
    CHECK(parse(ctx, "p > @0") == AP_OK);                   /* 1.x: index -1 */
    CHECK(parse(ctx, "a > b > c") == AP_OK);                /* ">" is a sound in the output */

    /* refused forms */
    CHECK(parse(ctx, "") == AP_ERR_PARSE);
    CHECK(parse(ctx, " > b") == AP_ERR_PARSE);
    CHECK(parse(ctx, "a b") == AP_ERR_PARSE);
    CHECK(parse(ctx, "a >") == AP_ERR_PARSE);
    CHECK(parse(ctx, "a > b /") == AP_ERR_PARSE);
    CHECK(parse(ctx, "a > b / c") == AP_ERR_PARSE);         /* no focus */
    CHECK(parse(ctx, "a > b / _ _") == AP_ERR_PARSE);       /* two foci */
    CHECK(parse(ctx, "C > @1[+voiced] / _.onset") == AP_ERR_PARSE); /* 1.x: _.onset is not a focus */
    CHECK(parse(ctx, "p|t > b|d") == AP_ERR_PARSE);         /* 3fdb52b: choice in the output */
    CHECK(parse(ctx, "a > {b|c}") == AP_ERR_PARSE);         /* more sets out than in */

    /* the token tree */
    check_json(ctx, "p > b / V _",
        "{\"source\":\"p > b / V _\",\"left_len\":1,\"right_len\":0,\"ante\":["
        "{\"kind\":\"segment\",\"id\":@,\"grapheme\":\"V\",\"features\":[\"vowel\"],\"partial\":true},"
        "{\"kind\":\"segment\",\"id\":@,\"grapheme\":\"p\",\"features\":[\"bilabial\",\"consonant\",\"stop\",\"voiceless\"],\"partial\":false}],"
        "\"post\":[{\"kind\":\"backref\",\"index\":0,\"modifier\":null},"
        "{\"kind\":\"segment\",\"id\":@,\"grapheme\":\"b\",\"features\":[\"bilabial\",\"consonant\",\"stop\",\"voiced\"],\"partial\":false}]}");
    check_json(ctx, "!# C? > @1[+voiced] :null:",
        "{\"source\":\"!# C? > @1[+voiced] :null:\",\"left_len\":0,\"right_len\":0,\"ante\":["
        "{\"kind\":\"negation\",\"inner\":{\"kind\":\"boundary\"}},"
        "{\"kind\":\"quantified\",\"quantifier\":\"?\",\"inner\":{\"kind\":\"segment\",\"id\":@,\"grapheme\":\"C\",\"features\":[\"consonant\"],\"partial\":true}}],"
        "\"post\":[{\"kind\":\"backref\",\"index\":0,\"modifier\":\"+voiced\"},{\"kind\":\"empty\"}]}");

    /* sequences */
    CHECK(ap_parse_sequence(ctx, "# a p a #", buf, 8, &n, NULL) == AP_OK && n == 5);
    CHECK(buf[0] == AP_SEG_BOUNDARY && buf[4] == AP_SEG_BOUNDARY && buf[1] == buf[3]);
    CHECK(ap_parse_sequence(ctx, "a a a a a a a a a", buf, 8, &n, NULL) == AP_ERR_BUFFER_TOO_SMALL && n == 9);
    CHECK(ap_parse_sequence(ctx, "", buf, 8, &n, NULL) == AP_OK && n == 0);
    CHECK(ap_parse_sequence(ctx, " \t ", buf, 8, &n, NULL) == AP_OK && n == 0);
    {
        char *text = NULL;
        CHECK(ap_parse_sequence(ctx, "# e\xcc\x81 g #", buf, 8, &n, NULL) == AP_OK && n == 4);
        CHECK(ap_render_sequence(ctx, buf, n, &text) == AP_OK);
        CHECK(text != NULL && strcmp(text, "# e\xcc\x81 g #") == 0);
        ap_free(text);
        CHECK(ap_parse_sequence(ctx, "# \xc3\xa9 #", buf, 8, &n, NULL) == AP_OK && n == 3); /* NFC é -> NFD */
        CHECK(ap_render_sequence(ctx, buf, n, &text) == AP_OK);
        CHECK(text != NULL && strcmp(text, "# e\xcc\x81 #") == 0);
        ap_free(text);
    }

    ap_context_free(ctx);
    return test_finish("parser");
}
