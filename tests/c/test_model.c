/* The change-model scorer: pack loading and refusals, and eta on a pack whose
 * answers can be worked out by hand. The agreement with the Python fitter on
 * real data is tests/parity/model_parity.py (needs the fetched data). */

#include "helpers.h"

#include <math.h>

static char *labels_line(void)
{
    const mk_system *sys = NULL;
    mk_string_list *labels = NULL;
    size_t i;
    size_t n;
    size_t len = 16;
    char *out;

    mk_registry_get_system(test_registry, "descriptive", &sys);
    mk_system_vector_labels(sys, &labels);
    n = mk_string_list_size(labels);
    for (i = 0; i < n; i++) {
        len += strlen(mk_string_list_get(labels, i)) + 1;
    }
    out = (char *)malloc(len);
    strcpy(out, "labels");
    for (i = 0; i < n; i++) {
        strcat(out, "\t");
        strcat(out, mk_string_list_get(labels, i));
    }
    mk_string_list_free(labels);
    return out;
}

static ap_model *load(ap_context *ctx, const char *body, ap_status *st)
{
    char *labels = labels_line();
    size_t len = strlen(labels) + strlen(body) + 128;
    char *text = (char *)malloc(len);
    ap_model *m = NULL;

    snprintf(text, len, "alteruphono-change-model\t1\nsystem\tdescriptive\n%s\n%s", labels, body);
    *st = ap_model_load(ctx, text, strlen(text), &m, NULL);
    free(labels);
    free(text);
    return m;
}

int main(void)
{
    ap_context *ctx = test_context();
    ap_model *m;
    ap_status st;
    double eta[4];
    double lp[4];
    const char *const cands[4] = { "p", "b", "-", "f" };

    /* refusals */
    CHECK(ap_model_load(ctx, "nonsense", 8, &m, NULL) == AP_ERR_MODEL_FORMAT && m == NULL);
    CHECK(ap_model_load(ctx, "alteruphono-change-model\t2\n", 26, &m, NULL) == AP_ERR_MODEL_FORMAT);
    {
        const char *bad = "alteruphono-change-model\t1\nlabels\tvoice\tnot-a-label\n";
        CHECK(ap_model_load(ctx, bad, strlen(bad), &m, NULL) == AP_ERR_INCOMPATIBLE);
    }
    m = load(ctx, "param\tno_such_parameter\t1.0\n", &st);
    CHECK(st == AP_ERR_MODEL_FORMAT && m == NULL);

    /* only intercepts: every change gets a_sub, deletion a_del, staying 0 */
    m = load(ctx, "param\ta_sub\t-1.5\nparam\ta_del\t-2.5\n", &st);
    CHECK(st == AP_OK && m != NULL);
    CHECK(ap_model_eta(m, ctx, "p", "a", "a", cands, 4, 0.0, eta) == AP_OK);
    CHECK(eta[0] == 0.0 && fabs(eta[1] + 1.5) < 1e-12 && fabs(eta[2] + 2.5) < 1e-12 && fabs(eta[3] + 1.5) < 1e-12);
    /* the branch offset moves every change, never staying */
    CHECK(ap_model_eta(m, ctx, "p", "a", "a", cands, 4, 1.0, eta) == AP_OK);
    CHECK(eta[0] == 0.0 && fabs(eta[1] + 0.5) < 1e-12 && fabs(eta[2] + 1.5) < 1e-12);
    CHECK(ap_model_logprob(m, ctx, "p", "a", "a", cands, 4, 0.0, lp) == AP_OK);
    CHECK(fabs(exp(lp[0]) + exp(lp[1]) + exp(lp[2]) + exp(lp[3]) - 1.0) < 1e-12);
    /* another context is refused */
    {
        ap_context *other = test_context();
        CHECK(ap_model_eta(m, other, "p", "a", "a", cands, 4, 0.0, eta) == AP_ERR_INVALID_ARGUMENT);
        ap_context_free(other);
    }
    ap_model_free(m);

    /* the distance base and the voicing direction: p -> b is one step up in voice */
    m = load(ctx, "param\tbeta\t2.0\nparam\tw:voice:up\t0.75\nparam\tw:voice:down\t-9\n", &st);
    CHECK(st == AP_OK);
    CHECK(ap_model_eta(m, ctx, "p", "#", "#", cands, 4, 0.0, eta) == AP_OK);
    {
        const mk_system *sys = NULL;
        double d = 0.0;
        mk_registry_get_system(test_registry, "descriptive", &sys);
        mk_system_segment_distance(sys, "p", "b", &d);
        CHECK(fabs(eta[1] - (0.75 - 2.0 * d)) < 1e-12);
    }
    {
        const char *const rev[2] = { "b", "p" };
        double e2[2];
        CHECK(ap_model_eta(m, ctx, "b", "#", "#", rev, 2, 0.0, e2) == AP_OK);
        CHECK(e2[1] < -9.0); /* b -> p goes down in voice: a different parameter */
    }
    ap_model_free(m);

    /* the catalogue term: a rule p > b between vowels adds lam * log(1 + 2) there only */
    m = load(ctx, "param\tlam\t1.0\nrule\t2.0\tp > b / V _ V\nrule\t1.0\tthis is not a rule\n", &st);
    CHECK(st == AP_OK);
    CHECK(ap_model_eta(m, ctx, "p", "a", "a", cands, 4, 0.0, eta) == AP_OK);
    CHECK(fabs(eta[1] - log1p(2.0)) < 1e-12 && eta[3] == 0.0);
    CHECK(ap_model_eta(m, ctx, "p", "#", "a", cands, 4, 0.0, eta) == AP_OK);
    CHECK(eta[1] == 0.0);
    ap_model_free(m);

    ap_context_free(ctx);
    return test_finish("model");
}
