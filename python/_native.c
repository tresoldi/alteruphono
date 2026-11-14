/* alteruphono._native: the C engine behind the 1.x Python API.
 *
 * Handles are capsules: a context (owning a merkmal registry and an
 * ap_context) and rules (which keep their context alive). Sequences cross as
 * lists of segment ids; the Python layer (alteruphono/_core.py) maps ids to
 * the 1.x Sound and Boundary objects. Limited API, abi3, Python >= 3.12. */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "alteruphono.h"

#include <stdlib.h>
#include <string.h>

#define CTX_NAME "alteruphono._native.context"
#define RULE_NAME "alteruphono._native.rule"

typedef struct native_ctx {
    mk_registry *registry;
    ap_context *ctx;
} native_ctx;

static void ctx_destroy(PyObject *capsule)
{
    native_ctx *n = (native_ctx *)PyCapsule_GetPointer(capsule, CTX_NAME);

    if (n != NULL) {
        ap_context_free(n->ctx);
        mk_registry_free(n->registry);
        free(n);
    }
}

static void rule_destroy(PyObject *capsule)
{
    ap_rule *r = (ap_rule *)PyCapsule_GetPointer(capsule, RULE_NAME);
    PyObject *ctx = (PyObject *)PyCapsule_GetContext(capsule);

    ap_rule_free(r);
    Py_XDECREF(ctx);
}

static native_ctx *get_ctx(PyObject *obj)
{
    return (native_ctx *)PyCapsule_GetPointer(obj, CTX_NAME);
}

static PyObject *raise_status(ap_status st, const ap_diagnosis *d, PyObject *rule_error)
{
    const char *msg = (d != NULL && d->message[0] != '\0') ? d->message : ap_status_string(st);

    switch (st) {
    case AP_ERR_PARSE:
    case AP_ERR_INVALID_ARGUMENT:
        PyErr_SetString(PyExc_ValueError, msg);
        break;
    case AP_ERR_RULE:
        PyErr_SetString(rule_error != NULL ? rule_error : PyExc_ValueError, msg);
        break;
    case AP_ERR_OOM:
        PyErr_NoMemory();
        break;
    case AP_ERR_LIMIT:
        PyErr_SetString(PyExc_OverflowError, msg);
        break;
    default:
        PyErr_SetString(PyExc_RuntimeError, msg);
        break;
    }
    return NULL;
}

static PyObject *new_context(PyObject *self, PyObject *args)
{
    const char *system = "descriptive";
    native_ctx *n;
    const mk_system *sys = NULL;
    ap_diagnosis d;
    ap_status st;
    PyObject *cap;

    (void)self;
    if (!PyArg_ParseTuple(args, "|s", &system)) {
        return NULL;
    }
    n = (native_ctx *)calloc(1, sizeof(native_ctx));
    if (n == NULL) {
        return PyErr_NoMemory();
    }
    if (mk_registry_new_builtin(&n->registry) != MK_OK) {
        free(n);
        PyErr_SetString(PyExc_RuntimeError, "cannot create a merkmal registry");
        return NULL;
    }
    if (mk_registry_get_system(n->registry, system, &sys) != MK_OK) {
        mk_registry_free(n->registry);
        free(n);
        PyErr_Format(PyExc_KeyError, "merkmal has no system %s", system);
        return NULL;
    }
    memset(&d, 0, sizeof(d));
    st = ap_context_new(sys, NULL, &n->ctx, &d);
    if (st != AP_OK) {
        mk_registry_free(n->registry);
        free(n);
        return raise_status(st, &d, NULL);
    }
    cap = PyCapsule_New(n, CTX_NAME, ctx_destroy);
    if (cap == NULL) {
        ap_context_free(n->ctx);
        mk_registry_free(n->registry);
        free(n);
    }
    return cap;
}

static PyObject *parse_rule(PyObject *self, PyObject *args)
{
    PyObject *cap;
    const char *text;
    native_ctx *n;
    ap_rule *rule = NULL;
    ap_diagnosis d;
    ap_status st;
    char *json = NULL;
    PyObject *rcap;
    PyObject *res;

    (void)self;
    if (!PyArg_ParseTuple(args, "Os", &cap, &text) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    memset(&d, 0, sizeof(d));
    st = ap_rule_parse(n->ctx, text, &rule, &d);
    if (st != AP_OK) {
        return raise_status(st, &d, NULL);
    }
    st = ap_rule_to_json(n->ctx, rule, &json);
    if (st != AP_OK) {
        ap_rule_free(rule);
        return raise_status(st, NULL, NULL);
    }
    rcap = PyCapsule_New(rule, RULE_NAME, rule_destroy);
    if (rcap == NULL) {
        ap_rule_free(rule);
        ap_free(json);
        return NULL;
    }
    Py_INCREF(cap);
    PyCapsule_SetContext(rcap, cap);
    res = Py_BuildValue("(Ns)", rcap, json);
    ap_free(json);
    return res;
}

static PyObject *ids_to_list(const ap_seg *ids, size_t n)
{
    PyObject *list = PyList_New((Py_ssize_t)n);
    size_t i;

    if (list == NULL) {
        return NULL;
    }
    for (i = 0; i < n; i++) {
        PyObject *v = PyLong_FromUnsignedLong((unsigned long)ids[i]);
        if (v == NULL) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SetItem(list, (Py_ssize_t)i, v);
    }
    return list;
}

/* A Python sequence of ints to a malloc'd id array. */
static ap_seg *list_to_ids(PyObject *seq, size_t *n)
{
    PyObject *fast = PySequence_Fast(seq, "expected a sequence of segment ids");
    Py_ssize_t len;
    Py_ssize_t i;
    ap_seg *ids;

    if (fast == NULL) {
        return NULL;
    }
    len = PySequence_Size(fast);
    ids = (ap_seg *)malloc(((size_t)len + 1) * sizeof(ap_seg));
    if (ids == NULL) {
        Py_DECREF(fast);
        PyErr_NoMemory();
        return NULL;
    }
    for (i = 0; i < len; i++) {
        PyObject *item = PySequence_GetItem(fast, i);
        unsigned long v;
        if (item == NULL) {
            free(ids);
            Py_DECREF(fast);
            return NULL;
        }
        v = PyLong_AsUnsignedLong(item);
        Py_DECREF(item);
        if (PyErr_Occurred()) {
            free(ids);
            Py_DECREF(fast);
            return NULL;
        }
        ids[i] = (ap_seg)v;
    }
    Py_DECREF(fast);
    *n = (size_t)len;
    return ids;
}

static PyObject *parse_sequence(PyObject *self, PyObject *args)
{
    PyObject *cap;
    const char *text;
    native_ctx *n;
    ap_seg stack[256];
    ap_seg *buf = stack;
    size_t len = 0;
    ap_status st;
    PyObject *res;

    (void)self;
    if (!PyArg_ParseTuple(args, "Os", &cap, &text) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    st = ap_parse_sequence(n->ctx, text, buf, 256, &len, NULL);
    if (st == AP_ERR_BUFFER_TOO_SMALL) {
        buf = (ap_seg *)malloc(len * sizeof(ap_seg));
        if (buf == NULL) {
            return PyErr_NoMemory();
        }
        st = ap_parse_sequence(n->ctx, text, buf, len, &len, NULL);
    }
    if (st != AP_OK) {
        if (buf != stack) {
            free(buf);
        }
        return raise_status(st, NULL, NULL);
    }
    res = ids_to_list(buf, len);
    if (buf != stack) {
        free(buf);
    }
    return res;
}

static PyObject *labels_tuple(char **labels, size_t n)
{
    PyObject *t = PyTuple_New((Py_ssize_t)n);
    size_t i;

    if (t == NULL) {
        return NULL;
    }
    for (i = 0; i < n; i++) {
        PyObject *s = PyUnicode_FromString(labels[i]);
        if (s == NULL) {
            Py_DECREF(t);
            return NULL;
        }
        PyTuple_SetItem(t, (Py_ssize_t)i, s);
    }
    return t;
}

static PyObject *seg_info(PyObject *self, PyObject *args)
{
    PyObject *cap;
    unsigned long id;
    native_ctx *n;
    const char *g = NULL;
    char **labels = NULL;
    size_t count = 0;
    int partial = 0;
    ap_status st;
    PyObject *t;

    (void)self;
    if (!PyArg_ParseTuple(args, "Ok", &cap, &id) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    st = ap_seg_grapheme(n->ctx, (ap_seg)id, &g);
    if (st == AP_OK) {
        st = ap_seg_is_partial(n->ctx, (ap_seg)id, &partial);
    }
    if (st == AP_OK) {
        st = ap_seg_labels(n->ctx, (ap_seg)id, &labels, &count);
    }
    if (st != AP_OK) {
        return raise_status(st, NULL, NULL);
    }
    t = labels_tuple(labels, count);
    ap_strings_free(labels, count);
    if (t == NULL) {
        return NULL;
    }
    return Py_BuildValue("(sNO)", g, t, partial ? Py_True : Py_False);
}

/* intern(ctx, grapheme) -> id (1.x features.sound), or
 * intern(ctx, grapheme, labels, partial) -> id (an explicit Sound) */
static PyObject *intern(PyObject *self, PyObject *args)
{
    PyObject *cap;
    const char *g;
    PyObject *labels = NULL;
    int partial = 0;
    native_ctx *n;
    ap_seg out = 0;
    ap_status st;

    (void)self;
    if (!PyArg_ParseTuple(args, "Os|Op", &cap, &g, &labels, &partial) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    if (labels == NULL || labels == Py_None) {
        st = ap_intern(n->ctx, g, &out);
    } else {
        PyObject *fast = PySequence_Fast(labels, "labels must be a sequence of str");
        Py_ssize_t len;
        Py_ssize_t i;
        const char **arr;
        if (fast == NULL) {
            return NULL;
        }
        len = PySequence_Size(fast);
        arr = (const char **)malloc(((size_t)len + 1) * sizeof(char *));
        if (arr == NULL) {
            Py_DECREF(fast);
            return PyErr_NoMemory();
        }
        for (i = 0; i < len; i++) {
            PyObject *item = PySequence_GetItem(fast, i); /* new ref; the list keeps it alive */
            arr[i] = item != NULL ? PyUnicode_AsUTF8AndSize(item, NULL) : NULL;
            Py_XDECREF(item);
            if (arr[i] == NULL) {
                free(arr);
                Py_DECREF(fast);
                return NULL;
            }
        }
        st = ap_intern_labels(n->ctx, g, arr, (size_t)len, partial, &out);
        free(arr);
        Py_DECREF(fast);
    }
    if (st != AP_OK) {
        return raise_status(st, NULL, NULL);
    }
    return PyLong_FromUnsignedLong((unsigned long)out);
}

static ap_rule *get_rule(PyObject *rcap, native_ctx *n)
{
    ap_rule *r = (ap_rule *)PyCapsule_GetPointer(rcap, RULE_NAME);

    if (r != NULL && get_ctx((PyObject *)PyCapsule_GetContext(rcap)) != n) {
        PyErr_SetString(PyExc_ValueError, "rule belongs to another context");
        return NULL;
    }
    return r;
}

static PyObject *do_forward(native_ctx *n, ap_rule *r, const ap_seg *in, size_t len)
{
    ap_seg stack[512];
    ap_seg *out = stack;
    size_t cap = 512;
    size_t w = 0;
    ap_status st = ap_forward(n->ctx, r, in, len, out, cap, &w);
    PyObject *res;

    if (st == AP_ERR_BUFFER_TOO_SMALL) {
        out = (ap_seg *)malloc(w * sizeof(ap_seg));
        if (out == NULL) {
            return PyErr_NoMemory();
        }
        cap = w;
        st = ap_forward(n->ctx, r, in, len, out, cap, &w);
    }
    if (st != AP_OK) {
        if (out != stack) {
            free(out);
        }
        return raise_status(st, NULL, PyExc_ValueError);
    }
    res = ids_to_list(out, w);
    if (out != stack) {
        free(out);
    }
    return res;
}

static PyObject *forward(PyObject *self, PyObject *args)
{
    PyObject *cap;
    PyObject *rcap;
    PyObject *seq;
    native_ctx *n;
    ap_rule *r;
    ap_seg *in;
    size_t len = 0;
    PyObject *res;

    (void)self;
    if (!PyArg_ParseTuple(args, "OOO", &cap, &rcap, &seq) || (n = get_ctx(cap)) == NULL
        || (r = get_rule(rcap, n)) == NULL) {
        return NULL;
    }
    if ((in = list_to_ids(seq, &len)) == NULL) {
        return NULL;
    }
    res = do_forward(n, r, in, len);
    free(in);
    return res;
}

static PyObject *forward_many(PyObject *self, PyObject *args)
{
    PyObject *cap;
    PyObject *rcap;
    PyObject *seqs;
    PyObject *fast;
    PyObject *out;
    native_ctx *n;
    ap_rule *r;
    Py_ssize_t count;
    Py_ssize_t i;

    (void)self;
    if (!PyArg_ParseTuple(args, "OOO", &cap, &rcap, &seqs) || (n = get_ctx(cap)) == NULL
        || (r = get_rule(rcap, n)) == NULL) {
        return NULL;
    }
    fast = PySequence_Fast(seqs, "expected a sequence of sequences");
    if (fast == NULL) {
        return NULL;
    }
    count = PySequence_Size(fast);
    out = PyList_New(count);
    if (out == NULL) {
        Py_DECREF(fast);
        return NULL;
    }
    for (i = 0; i < count; i++) {
        PyObject *item = PySequence_GetItem(fast, i);
        ap_seg *in;
        size_t len = 0;
        PyObject *res;
        if (item == NULL) {
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }
        in = list_to_ids(item, &len);
        Py_DECREF(item);
        if (in == NULL) {
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }
        res = do_forward(n, r, in, len);
        free(in);
        if (res == NULL) {
            Py_DECREF(out);
            Py_DECREF(fast);
            return NULL;
        }
        PyList_SetItem(out, i, res);
    }
    Py_DECREF(fast);
    return out;
}


/* ---- object fast paths ------------------------------------------------------
 * forward_objs/backward_objs take and return the 1.x Python objects directly:
 * a Sound's engine id is read from its `_ap_id` attribute and output ids are
 * mapped through the caller's id -> object list. Either returns None (no
 * exception) when an input has no id yet or an output id has no object yet;
 * the Python layer then interns or creates them and calls again. */

static PyObject *ap_id_name = NULL;

/* 1: ids filled; 0: some element has no id (no exception); -1: error */
static int objs_to_ids(PyObject *seq, PyObject *boundary_type, ap_seg **out, size_t *n)
{
    PyObject *fast = PySequence_Fast(seq, "expected a sequence");
    Py_ssize_t len;
    Py_ssize_t i;
    ap_seg *ids;

    if (fast == NULL) {
        return -1;
    }
    len = PySequence_Size(fast);
    ids = (ap_seg *)malloc(((size_t)len + 1) * sizeof(ap_seg));
    if (ids == NULL) {
        Py_DECREF(fast);
        PyErr_NoMemory();
        return -1;
    }
    for (i = 0; i < len; i++) {
        PyObject *item = PySequence_GetItem(fast, i);
        PyObject *v;
        int is_b;
        if (item == NULL) {
            free(ids);
            Py_DECREF(fast);
            return -1;
        }
        is_b = PyObject_IsInstance(item, boundary_type);
        if (is_b < 0) {
            Py_DECREF(item);
            free(ids);
            Py_DECREF(fast);
            return -1;
        }
        if (is_b) {
            ids[i] = AP_SEG_BOUNDARY;
            Py_DECREF(item);
            continue;
        }
        v = PyObject_GetAttr(item, ap_id_name);
        Py_DECREF(item);
        if (v == NULL) {
            PyErr_Clear();
            free(ids);
            Py_DECREF(fast);
            return 0;
        }
        ids[i] = (ap_seg)PyLong_AsUnsignedLong(v);
        Py_DECREF(v);
        if (PyErr_Occurred()) {
            free(ids);
            Py_DECREF(fast);
            return -1;
        }
    }
    Py_DECREF(fast);
    *out = ids;
    *n = (size_t)len;
    return 1;
}

/* A tuple of objects for ids, or NULL with no exception when one is missing. */
static PyObject *ids_to_objs(const ap_seg *ids, size_t n, PyObject *objects)
{
    PyObject *t = PyTuple_New((Py_ssize_t)n);
    Py_ssize_t have = PyList_Size(objects);
    size_t i;

    if (t == NULL) {
        return NULL;
    }
    for (i = 0; i < n; i++) {
        PyObject *o;
        if ((Py_ssize_t)ids[i] >= have || (o = PyList_GetItem(objects, (Py_ssize_t)ids[i])) == NULL
            || o == Py_None) {
            PyErr_Clear();
            Py_DECREF(t);
            return NULL;
        }
        Py_INCREF(o);
        PyTuple_SetItem(t, (Py_ssize_t)i, o);
    }
    return t;
}

static PyObject *forward_objs(PyObject *self, PyObject *args)
{
    PyObject *cap;
    PyObject *rcap;
    PyObject *seq;
    PyObject *objects;
    PyObject *btype;
    native_ctx *n;
    ap_rule *r;
    ap_seg *in = NULL;
    size_t len = 0;
    ap_seg stack[512];
    ap_seg *out = stack;
    size_t w = 0;
    ap_status st;
    int got;
    PyObject *res;

    (void)self;
    if (!PyArg_ParseTuple(args, "OOOOO", &cap, &rcap, &seq, &objects, &btype) || (n = get_ctx(cap)) == NULL
        || (r = get_rule(rcap, n)) == NULL) {
        return NULL;
    }
    got = objs_to_ids(seq, btype, &in, &len);
    if (got <= 0) {
        if (got < 0) {
            return NULL;
        }
        Py_RETURN_NONE;
    }
    st = ap_forward(n->ctx, r, in, len, out, 512, &w);
    if (st == AP_ERR_BUFFER_TOO_SMALL) {
        out = (ap_seg *)malloc(w * sizeof(ap_seg));
        if (out == NULL) {
            free(in);
            return PyErr_NoMemory();
        }
        st = ap_forward(n->ctx, r, in, len, out, w, &w);
    }
    free(in);
    if (st != AP_OK) {
        if (out != stack) {
            free(out);
        }
        return raise_status(st, NULL, PyExc_ValueError);
    }
    res = ids_to_objs(out, w, objects);
    if (res == NULL && !PyErr_Occurred()) {
        /* new segments: hand back the ids for the Python layer to map */
        res = ids_to_list(out, w);
    }
    if (out != stack) {
        free(out);
    }
    return res;
}

static PyObject *backward(PyObject *self, PyObject *args)
{
    PyObject *cap;
    PyObject *rcap;
    PyObject *seq;
    native_ctx *n;
    ap_rule *r;
    ap_seg *in;
    size_t len = 0;
    ap_candidates *c = NULL;
    ap_status st;
    PyObject *out;
    size_t i;

    (void)self;
    if (!PyArg_ParseTuple(args, "OOO", &cap, &rcap, &seq) || (n = get_ctx(cap)) == NULL
        || (r = get_rule(rcap, n)) == NULL) {
        return NULL;
    }
    if ((in = list_to_ids(seq, &len)) == NULL) {
        return NULL;
    }
    st = ap_backward(n->ctx, r, in, len, &c);
    free(in);
    if (st != AP_OK) {
        return raise_status(st, NULL, PyExc_IndexError);
    }
    out = PyList_New((Py_ssize_t)ap_candidates_count(c));
    if (out == NULL) {
        ap_candidates_free(c);
        return NULL;
    }
    for (i = 0; i < ap_candidates_count(c); i++) {
        const ap_seg *s;
        size_t sl;
        PyObject *l;
        ap_candidates_get(c, i, &s, &sl);
        l = ids_to_list(s, sl);
        if (l == NULL) {
            Py_DECREF(out);
            ap_candidates_free(c);
            return NULL;
        }
        PyList_SetItem(out, (Py_ssize_t)i, l);
    }
    ap_candidates_free(c);
    return out;
}


static PyObject *backward_objs(PyObject *self, PyObject *args)
{
    PyObject *cap;
    PyObject *rcap;
    PyObject *seq;
    PyObject *objects;
    PyObject *btype;
    native_ctx *n;
    ap_rule *r;
    ap_seg *in = NULL;
    size_t len = 0;
    ap_candidates *c = NULL;
    ap_status st;
    int got;
    PyObject *out;
    size_t i;
    int complete = 1;

    (void)self;
    if (!PyArg_ParseTuple(args, "OOOOO", &cap, &rcap, &seq, &objects, &btype) || (n = get_ctx(cap)) == NULL
        || (r = get_rule(rcap, n)) == NULL) {
        return NULL;
    }
    got = objs_to_ids(seq, btype, &in, &len);
    if (got <= 0) {
        if (got < 0) {
            return NULL;
        }
        Py_RETURN_NONE;
    }
    st = ap_backward(n->ctx, r, in, len, &c);
    free(in);
    if (st != AP_OK) {
        return raise_status(st, NULL, PyExc_IndexError);
    }
    out = PyList_New((Py_ssize_t)ap_candidates_count(c));
    if (out == NULL) {
        ap_candidates_free(c);
        return NULL;
    }
    for (i = 0; i < ap_candidates_count(c); i++) {
        const ap_seg *sq;
        size_t sl;
        PyObject *t = NULL;
        ap_candidates_get(c, i, &sq, &sl);
        if (complete) {
            t = ids_to_objs(sq, sl, objects);
            if (t == NULL && PyErr_Occurred()) {
                Py_DECREF(out);
                ap_candidates_free(c);
                return NULL;
            }
            if (t == NULL) {
                complete = 0;
            }
        }
        if (t == NULL) {
            t = ids_to_list(sq, sl); /* the Python layer maps new ids */
            if (t == NULL) {
                Py_DECREF(out);
                ap_candidates_free(c);
                return NULL;
            }
        }
        PyList_SetItem(out, (Py_ssize_t)i, t);
    }
    ap_candidates_free(c);
    return out;
}

static PyObject *grapheme_features(PyObject *self, PyObject *args)
{
    PyObject *cap;
    const char *g;
    native_ctx *n;
    char **labels = NULL;
    size_t count = 0;
    int found = 0;
    ap_status st;
    PyObject *t;

    (void)self;
    if (!PyArg_ParseTuple(args, "Os", &cap, &g) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    st = ap_grapheme_features(n->ctx, g, &labels, &count, &found);
    if (st != AP_OK) {
        return raise_status(st, NULL, NULL);
    }
    if (!found) {
        Py_RETURN_NONE;
    }
    t = labels_tuple(labels, count);
    ap_strings_free(labels, count);
    return t;
}

static PyObject *class_features(PyObject *self, PyObject *args)
{
    PyObject *cap;
    const char *g;
    native_ctx *n;
    char **labels = NULL;
    size_t count = 0;
    int found = 0;
    ap_status st;
    PyObject *t;

    (void)self;
    if (!PyArg_ParseTuple(args, "Os", &cap, &g) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    st = ap_class_features(n->ctx, g, &labels, &count, &found);
    if (st != AP_OK) {
        return raise_status(st, NULL, NULL);
    }
    if (!found) {
        Py_RETURN_NONE;
    }
    t = labels_tuple(labels, count);
    ap_strings_free(labels, count);
    return t;
}

static PyObject *features_grapheme(PyObject *self, PyObject *args)
{
    PyObject *cap;
    PyObject *labels;
    PyObject *fast;
    native_ctx *n;
    Py_ssize_t len;
    Py_ssize_t i;
    const char **arr;
    const char *g = NULL;
    int found = 0;
    ap_status st;

    (void)self;
    if (!PyArg_ParseTuple(args, "OO", &cap, &labels) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    fast = PySequence_Fast(labels, "labels must be a sequence of str");
    if (fast == NULL) {
        return NULL;
    }
    len = PySequence_Size(fast);
    arr = (const char **)malloc(((size_t)len + 1) * sizeof(char *));
    if (arr == NULL) {
        Py_DECREF(fast);
        return PyErr_NoMemory();
    }
    for (i = 0; i < len; i++) {
        PyObject *item = PySequence_GetItem(fast, i);
        arr[i] = item != NULL ? PyUnicode_AsUTF8AndSize(item, NULL) : NULL;
        Py_XDECREF(item);
        if (arr[i] == NULL) {
            free(arr);
            Py_DECREF(fast);
            return NULL;
        }
    }
    st = ap_features_grapheme(n->ctx, arr, (size_t)len, &g, &found);
    free(arr);
    Py_DECREF(fast);
    if (st != AP_OK) {
        return raise_status(st, NULL, NULL);
    }
    if (!found) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(g);
}


/* ---- the change model ---------------------------------------------------- */

#define MODEL_NAME "alteruphono._native.model"

static void model_destroy(PyObject *capsule)
{
    ap_model *m = (ap_model *)PyCapsule_GetPointer(capsule, MODEL_NAME);
    PyObject *ctx = (PyObject *)PyCapsule_GetContext(capsule);

    ap_model_free(m);
    Py_XDECREF(ctx);
}

static PyObject *model_load(PyObject *self, PyObject *args)
{
    PyObject *cap;
    const char *text;
    Py_ssize_t len;
    native_ctx *n;
    ap_model *m = NULL;
    ap_diagnosis d;
    ap_status st;
    PyObject *mcap;

    (void)self;
    if (!PyArg_ParseTuple(args, "Os#", &cap, &text, &len) || (n = get_ctx(cap)) == NULL) {
        return NULL;
    }
    memset(&d, 0, sizeof(d));
    st = ap_model_load(n->ctx, text, (size_t)len, &m, &d);
    if (st != AP_OK) {
        return raise_status(st, &d, NULL);
    }
    mcap = PyCapsule_New(m, MODEL_NAME, model_destroy);
    if (mcap == NULL) {
        ap_model_free(m);
        return NULL;
    }
    Py_INCREF(cap);
    PyCapsule_SetContext(mcap, cap);
    return mcap;
}

static PyObject *model_score(PyObject *args, int logprob)
{
    PyObject *cap;
    PyObject *mcap;
    PyObject *cands;
    PyObject *fast;
    const char *s;
    const char *l;
    const char *r;
    double offset = 0.0;
    native_ctx *n;
    ap_model *m;
    Py_ssize_t k;
    Py_ssize_t i;
    const char **arr;
    double *out;
    ap_status st;
    PyObject *res;

    if (!PyArg_ParseTuple(args, "OOsssO|d", &cap, &mcap, &s, &l, &r, &cands, &offset) || (n = get_ctx(cap)) == NULL
        || (m = (ap_model *)PyCapsule_GetPointer(mcap, MODEL_NAME)) == NULL) {
        return NULL;
    }
    fast = PySequence_Fast(cands, "candidates must be a sequence of str");
    if (fast == NULL) {
        return NULL;
    }
    k = PySequence_Size(fast);
    arr = (const char **)malloc(((size_t)k + 1) * sizeof(char *));
    out = (double *)malloc(((size_t)k + 1) * sizeof(double));
    if (arr == NULL || out == NULL) {
        free(arr);
        free(out);
        Py_DECREF(fast);
        return PyErr_NoMemory();
    }
    for (i = 0; i < k; i++) {
        PyObject *item = PySequence_GetItem(fast, i);
        arr[i] = item != NULL ? PyUnicode_AsUTF8AndSize(item, NULL) : NULL;
        Py_XDECREF(item);
        if (arr[i] == NULL) {
            free(arr);
            free(out);
            Py_DECREF(fast);
            return NULL;
        }
    }
    st = logprob ? ap_model_logprob(m, n->ctx, s, l, r, arr, (size_t)k, offset, out)
                 : ap_model_eta(m, n->ctx, s, l, r, arr, (size_t)k, offset, out);
    free(arr);
    Py_DECREF(fast);
    if (st != AP_OK) {
        free(out);
        return raise_status(st, NULL, NULL);
    }
    res = PyList_New(k);
    for (i = 0; res != NULL && i < k; i++) {
        PyList_SetItem(res, i, PyFloat_FromDouble(out[i]));
    }
    free(out);
    return res;
}

static PyObject *model_eta(PyObject *self, PyObject *args)
{
    (void)self;
    return model_score(args, 0);
}

static PyObject *model_logprob(PyObject *self, PyObject *args)
{
    (void)self;
    return model_score(args, 1);
}

static PyObject *version(PyObject *self, PyObject *args)
{
    (void)self;
    (void)args;
    return Py_BuildValue("(sk)", ap_version_string(), (unsigned long)ap_abi_version());
}

static PyMethodDef methods[] = {
    { "new_context", new_context, METH_VARARGS, "new_context(system='descriptive') -> context" },
    { "parse_rule", parse_rule, METH_VARARGS, "parse_rule(ctx, text) -> (rule, json)" },
    { "parse_sequence", parse_sequence, METH_VARARGS, "parse_sequence(ctx, text) -> [id]" },
    { "seg_info", seg_info, METH_VARARGS, "seg_info(ctx, id) -> (grapheme, labels, partial)" },
    { "intern", intern, METH_VARARGS, "intern(ctx, grapheme[, labels, partial]) -> id" },
    { "forward", forward, METH_VARARGS, "forward(ctx, rule, [id]) -> [id]" },
    { "forward_objs", forward_objs, METH_VARARGS,
      "forward_objs(ctx, rule, seq, objects, Boundary) -> tuple | [id] | None" },
    { "backward_objs", backward_objs, METH_VARARGS,
      "backward_objs(ctx, rule, seq, objects, Boundary) -> [tuple | [id]] | None" },
    { "forward_many", forward_many, METH_VARARGS, "forward_many(ctx, rule, [[id]]) -> [[id]]" },
    { "backward", backward, METH_VARARGS, "backward(ctx, rule, [id]) -> [[id]]" },
    { "grapheme_features", grapheme_features, METH_VARARGS, "grapheme_features(ctx, g) -> labels | None" },
    { "class_features", class_features, METH_VARARGS, "class_features(ctx, name) -> labels | None" },
    { "features_grapheme", features_grapheme, METH_VARARGS, "features_grapheme(ctx, labels) -> str | None" },
    { "model_load", model_load, METH_VARARGS, "model_load(ctx, text) -> model" },
    { "model_eta", model_eta, METH_VARARGS, "model_eta(ctx, model, s, left, right, candidates[, offset]) -> [eta]" },
    { "model_logprob", model_logprob, METH_VARARGS,
      "model_logprob(ctx, model, s, left, right, candidates[, offset]) -> [log p]" },
    { "version", version, METH_NOARGS, "version() -> (version, abi)" },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "alteruphono._native", "The alteruphono C engine.", -1, methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__native(void);

PyMODINIT_FUNC PyInit__native(void)
{
    ap_id_name = PyUnicode_InternFromString("_ap_id");
    if (ap_id_name == NULL) {
        return NULL;
    }
    return PyModule_Create(&module);
}
