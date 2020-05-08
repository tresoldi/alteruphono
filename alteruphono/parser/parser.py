"""
Sound Change parser.
"""

# Import Python standard libraries
from pathlib import Path

# Import 3rd-party libraries
# TODO: should use traditional instead of clean PEG?
import arpeggio
from arpeggio.cleanpeg import ParserPEG

# TODO: compile a prettified grammar for saving some time on loading?
# TODO: check about debug options
# TODO: should memoize? -- almost surely yes
# TODO: should normalization be applied here?
# TODO: write auxiliary function for updating backrefs in ASTs?

from collections.abc import Mapping, Iterable

def isiter(value):
    return (
        isinstance(value, Iterable) and
        not isinstance(value, str)
    )

def asjson(obj, seen=None):
    if isinstance(obj, Mapping) or isiter(obj):
        # prevent traversal of recursive structures
        if seen is None:
            seen = set()
        elif id(obj) in seen:
            return '__RECURSIVE__'
        seen.add(id(obj))

    if hasattr(obj, '__json__') and type(obj) is not type:
        return obj.__json__()
    elif isinstance(obj, Mapping):
        result = {}
        for k, v in obj.items():
            try:
                result[k] = asjson(v, seen)
            except TypeError:
                debug('Unhashable key?', type(k), str(k))
                raise
        return result
    elif isiter(obj):
        return [asjson(e, seen) for e in obj]
    else:
        return obj

class AST(dict):
    _frozen = False

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)
        self._frozen = True

    @property
    def frozen(self):
        return self._frozen

#    @property
#    def parseinfo(self):
#        try:
#            return super().__getitem__('parseinfo')
#        except KeyError:
#            pass
#
#    def set_parseinfo(self, value):
#        super().__setitem__('parseinfo', value)

    def copy(self):
        return self.__copy__()

    def asjson(self):
        return asjson(self)

    def _set(self, key, value, force_list=False):
        key = self._safekey(key)
        previous = self.get(key)

        if previous is None and force_list:
            value = [value]
        elif previous is None:
            pass
        elif isinstance(previous, list):
            value = previous + [value]
        else:
            value = [previous, value]

        super().__setitem__(key, value)

    def _setlist(self, key, value):
        return self._set(key, value, force_list=True)

    def __copy__(self):
        return AST(self)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        key = self._safekey(key)
        if key in self:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        key = self._safekey(key)
        super().__delitem__(key)

    def __setattr__(self, name, value):
        if self._frozen and name not in vars(self):
            raise AttributeError(
                f'{type(self).__name__} attributes are fixed. '
                f' Cannot set attribute "{name}".'
            )
        super().__setattr__(name, value)

    def __getattr__(self, name):
        key = self._safekey(name)
        if key in self:
            return self[key]
        elif name in self:
            return self[name]

        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None

    def __hasattribute__(self, name):
        try:
            super().__getattribute__(name)
        except (TypeError, AttributeError):
            return False
        else:
            return True

    def __reduce__(self):
        return (AST, (), None, None, iter(self.items()))

    def _safekey(self, key):
        while self.__hasattribute__(key):
            key += '_'
        return key

    def _define(self, keys, list_keys=None):
        for key in keys:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, None)

        for key in list_keys or []:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, [])

    def __json__(self):
        return {
            name: asjson(value)
            for name, value in self.items()
        }

    def __repr__(self):
        return repr(self.asjson())

    def __str__(self):
        return str(self.asjson())

# Define Sound Change Visitor, for visiting the parse tree
class SC_Visitor(arpeggio.PTNodeVisitor):
    def visit_op_feature(self, node, children):
        return AST({'feature':children[1], 'value':children[0]})

    def visit_modifier(self, node, children):
        # don't collect square brackets
        return list(children[1])

    def visit_focus(self, node, children):
        return AST({'focus':node.value})

    def visit_choice(self, node, children):
        return list(children)

    def visit_boundary(self, node, children):
        return AST({'boundary':node.value})

    def visit_empty(self, node, children):
        return AST({'empty':node.value})

    def visit_backref(self, node, children):
        # return only the index as integer, along with any modifier
        if len(children) == 2:
            return AST({'backref':int(children[1])})
        else:
            return AST({'backref':int(children[1]), 'modifier':children[2]})

    def visit_sound_class(self, node, children):
        return AST({'sound_class':node.value})

    def visit_grapheme(self, node, children):
        return AST({'grapheme':node.value})

    # Don't capture `arrow`s
    def visit_arrow(self, node, children):
        pass

    # Don't capture `slash`es
    def visit_slash(self, node, children):
        pass

    # Sequences
    def visit_ante(self, node, children):
        return {'ante':list(children)}
    def visit_post(self, node, children):
        return {'post':list(children)}
    def visit_context(self, node, children):
        return {'context': list(children)}

    # Entry point
    def visit_rule(self, node, children):
        # Combine all subsquences, dealing with context optionality
        ret = {}
        for seq in children:
            ret.update(seq)

        return AST(ret)

class Parser:
    # Holds the real parser, loaded dinamically on first call
    _parser = None

    def __init__(self, debug=False):
        self.debug = debug

    def __call__(self, text):
        # Load and compile the grammar if necessary
        if not self._parser:
            self._load_grammar()

        # Parse the tree and visit each node
        ast = arpeggio.visit_parse_tree(self._parser.parse(text), SC_Visitor())

        # Apply all necessary post-processing and return
        return self._post_process(ast)

    def _post_process(self, ast):
        """
        Apply post-processing to an AST.
        """

        # The notation with context is necessary to follow the tradition,
        # making adoption and usage easier among linguists, but it makes our
        # processing much harder. Thus, we merge `.ante` and `.post` with the
        # `.context` (if any), already here at parsing stage, taking care of
        # issues such as indexes of back-references.
        # TODO: if the rule has alternatives, sound_classes, or other
        #       profilific rules in `context`, it might be necessary to
        #       perform a more complex merging and add back-references in
        #       `post` to what is matched in `ante`, which could potentially
        #       even mean different ASTs for forward and backward. This
        #       needs further and detailed investigation, or explicit
        #       exclusion of such rules (the user could always have the
        #       profilic rules in `ante` and `post`, manually doing what
        #       would be done here).

        # Just return if there is no context
        if not ast.get("context"):
            return ast

        merged_ast = AST({
            "ante" : _merge_context(ast.ante, ast.context),
            "post" : _merge_context(ast.post, ast.context, offset_ref=len(ast.ante)),
        })

        return merged_ast

    # TODO: add logging
    def _load_grammar(self):
        """
        Internal function for loading and compiling a grammar.
        """

        grammar_path = Path(__file__).parent /  "sound_change.ebnf"
        with open(grammar_path.as_posix()) as grammar:
            self._parser = ParserPEG(grammar.read(), 'rule', ws='\t ', debug=self.debug)

def _merge_context(ast, context, offset_ref=None):
    """
    Merge an `ante` or `post` AST with a `context`.

    The essentials of the function are to add the left context at the
    beginning and the right one at the endself.

    The most important operation is to fix the indexes of back-references, in
    case they are used. This is specified via the `offset_ref` numeric
    variable: if provided, back-references will be positively shifted
    according to it (as we need to know the length of the AST before the
    right context in what we are referring to).
    """

    # Split at the `focus` symbol of the context, which is mandatory. Note
    # that we don't use a list comprehension, but a loop, in order to
    # break as soon as the focus is found.
    for idx, token in enumerate(context):
        if isinstance(token, AST):
            if "focus" in token:
                break
    left, right = context[:idx], context[idx + 1 :]

    # cache the length of `left` and of `ast`
    offset_left = len(left)
    offset_ast = offset_left + len(ast)

    # Merge the provided AST with the contextual one
    # TODO: take care of backreferences in alternatives
    merged_ast = []
    for token in ast:
        # `p @2 / a _` --> `a p @3`
        if "backref" in token:
            token_dict = dict(token)
            token_dict["backref"] += offset_left
            merged_ast.append(AST(token_dict))
        else:
            merged_ast.append(token)

    # Apply the `offset_ref` if provided, using `offset_ast` otherwise,
    # to build the final mapping. This is mostly responsible for
    # turning `post` into a long series of back-references in most cases,
    # such as in "V s -> @1 z @1 / # p|b r _ t|d", where `post`
    # becomes "@1 @2 @3 @4 z @4 @6"
    if offset_ref:
        # Here we can just fill the backreferences, as there are no modifiers
        merged_ast = (
            [AST({"backref":i + 1}) for i, _ in enumerate(left)]
            + merged_ast
            + [
                AST({"backref": i + 1 + offset_left + offset_ref})
                for i, _ in enumerate(right)
            ]
        )
    else:
        merged_ast = left + merged_ast
        for token in right:
            if "backref" in token:
                token_dict = dict(token)
                token_dict["backref"] += offset_ast
                merged_ast.append(AST(token_dict))
            else:
                merged_ast.append(token)

    return merged_ast

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise ValueError("Should provide the rule and only the rule.")

    p = Parser()
    v = p(sys.argv[1])
    print(v)
