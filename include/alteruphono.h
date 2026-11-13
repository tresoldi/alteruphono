#ifndef ALTERUPHONO_H
#define ALTERUPHONO_H

/* alteruphono: sound-change rules applied forwards and backwards, on merkmal
 * feature systems.
 *
 * Conventions (see docs/v2/DESIGN.md section 3):
 * - Every call returns ap_status; results come back through out-parameters,
 *   which belong to the caller only on AP_OK.
 * - Accessors return borrowed pointers valid while their owner lives.
 * - Strings are NUL-terminated UTF-8. Rule and sequence text is normalized to
 *   NFD on the way in, as alteruphono 1.x does.
 * - No global mutable state. A context is used by one thread at a time; give
 *   another thread its own context (ap_context_new or ap_context_clone).
 */

#include <stddef.h>
#include <stdint.h>

#include "merkmal.h"

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32) && defined(ALTERUPHONO_SHARED)
#if defined(ALTERUPHONO_BUILDING_LIBRARY)
#define AP_API __declspec(dllexport)
#else
#define AP_API __declspec(dllimport)
#endif
#elif defined(__GNUC__) || defined(__clang__)
#define AP_API __attribute__((visibility("default")))
#else
#define AP_API
#endif

#define AP_VERSION_MAJOR 2
#define AP_VERSION_MINOR 0
#define AP_VERSION_PATCH 0
#define AP_VERSION_STRING "2.0.0.dev0"
/* Moves on any change to an exported struct layout, enum, signature or
 * ownership rule. */
#define AP_ABI_VERSION 1

typedef enum ap_status {
    AP_OK = 0,
    AP_ERR_INVALID_ARGUMENT,
    AP_ERR_OOM,
    AP_ERR_PARSE,
    AP_ERR_MERKMAL,
    AP_ERR_UNKNOWN_GRAPHEME,
    AP_ERR_UNKNOWN_FEATURE,
    AP_ERR_UNKNOWN_CLASS,
    AP_ERR_LIMIT,
    AP_ERR_BUFFER_TOO_SMALL,
    AP_ERR_MODEL_FORMAT,
    AP_ERR_INCOMPATIBLE,
    /* A rule that parses but cannot be applied to this input: a set in the
     * output with no matching set in the input, or a back-reference out of
     * range in backward. alteruphono 1.x raised ValueError or IndexError. */
    AP_ERR_RULE
} ap_status;

/* Static text. */
AP_API const char *ap_status_string(ap_status status);
AP_API const char *ap_version_string(void);
AP_API uint32_t ap_abi_version(void);

/* Caller-owned error detail. Every parser takes one; NULL is allowed. */
typedef struct ap_diagnosis {
    ap_status status;
    size_t offset;
    char message[256];
} ap_diagnosis;

typedef struct ap_context ap_context;
typedef struct ap_rule ap_rule;
typedef struct ap_candidates ap_candidates;

/* A segment is an interned id, valid within its context (and its clones, for
 * ids interned before the clone). */
typedef uint32_t ap_seg;
#define AP_SEG_BOUNDARY ((ap_seg)0)

typedef enum ap_projection {
    /* merkmal labels restricted to alteruphono 1.x's vocabulary, with 1.x's
     * categories and its grapheme universe: the parity mode
     * (docs/v2/DESIGN.md section 4.1). */
    AP_PROJECTION_ALTERUPHONO_1 = 0,
    /* every label of the merkmal system (reserved; not implemented in 2.0.0) */
    AP_PROJECTION_NATIVE = 1
} ap_projection;

typedef struct ap_context_options {
    ap_projection projection;
    /* Upper bound on backward candidates; beyond it ap_backward returns
     * AP_ERR_LIMIT instead of an exponential product. */
    size_t max_backward_candidates;
} ap_context_options;

AP_API void ap_context_options_init_defaults(ap_context_options *options);

/* `system` is borrowed: the merkmal registry that owns it must outlive the
 * context. NULL options means the defaults. */
AP_API ap_status ap_context_new(
    const mk_system *system,
    const ap_context_options *options,
    ap_context **out,
    ap_diagnosis *diagnosis
);
AP_API ap_status ap_context_clone(const ap_context *context, ap_context **out);
AP_API void ap_context_free(ap_context *context);

/* Segments. ap_intern is 1.x's features.sound(): the grapheme exactly as
 * given (no normalization), a sound class if it names one, else its features
 * from the projection, else a featureless segment. "#" is a segment here, not
 * the boundary (AP_SEG_BOUNDARY), as in 1.x. */
AP_API ap_status ap_intern(ap_context *context, const char *grapheme, ap_seg *out);
/* A segment with exactly these labels (1.x's Sound(grapheme, features, partial)).
 * Labels the context does not know are added to it (AP_ERR_LIMIT past 256). */
AP_API ap_status ap_intern_labels(
    ap_context *context, const char *grapheme, const char *const *labels, size_t count,
    int partial, ap_seg *out);
/* The features of a sound class of the context's class pack, as 1.x stores
 * them ("-x" names included). *found is 0 for a name that is not a class. */
AP_API ap_status ap_class_features(
    const ap_context *context, const char *name, char ***labels, size_t *count, int *found);
AP_API ap_status ap_seg_grapheme(const ap_context *context, ap_seg seg, const char **out);
AP_API ap_status ap_seg_is_partial(const ap_context *context, ap_seg seg, int *out);
/* Labels of a segment, sorted by code point. Free with ap_strings_free. */
AP_API ap_status ap_seg_labels(
    const ap_context *context, ap_seg seg, char ***labels, size_t *count);
AP_API void ap_strings_free(char **strings, size_t count);
AP_API void ap_free(void *pointer);

/* The 1.x feature-system calls, on the context's projection. A NULL result
 * (AP_OK with *found == 0) is 1.x's None. */
AP_API ap_status ap_grapheme_features(
    ap_context *context, const char *grapheme, char ***labels, size_t *count, int *found);
AP_API ap_status ap_features_grapheme(
    ap_context *context, const char *const *labels, size_t count, const char **out, int *found);

/* Sequences: space-separated text, "#" for a boundary. The caller's buffer;
 * AP_ERR_BUFFER_TOO_SMALL reports the needed length in *length. */
AP_API ap_status ap_parse_sequence(
    ap_context *context, const char *text,
    ap_seg *buffer, size_t capacity, size_t *length, ap_diagnosis *diagnosis);
/* Graphemes joined by single spaces; owned, free with ap_free. */
AP_API ap_status ap_render_sequence(
    const ap_context *context, const ap_seg *sequence, size_t length, char **out);

/* Rules. */
AP_API ap_status ap_rule_parse(
    ap_context *context, const char *text, ap_rule **out, ap_diagnosis *diagnosis);
AP_API void ap_rule_free(ap_rule *rule);
/* The rule's token tree as JSON (the shape of 1.x's Rule dataclass); owned. */
AP_API ap_status ap_rule_to_json(const ap_context *context, const ap_rule *rule, char **out);

/* Application. Output goes to the caller's buffer, as for ap_parse_sequence. */
AP_API ap_status ap_forward(
    ap_context *context, const ap_rule *rule,
    const ap_seg *input, size_t length,
    ap_seg *output, size_t capacity, size_t *written);

AP_API ap_status ap_backward(
    ap_context *context, const ap_rule *rule,
    const ap_seg *input, size_t length, ap_candidates **out);
AP_API size_t ap_candidates_count(const ap_candidates *candidates);
AP_API ap_status ap_candidates_get(
    const ap_candidates *candidates, size_t index, const ap_seg **sequence, size_t *length);
AP_API void ap_candidates_free(ap_candidates *candidates);

#ifdef __cplusplus
}
#endif

#endif
