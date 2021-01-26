import itertools

import maniphono

from .common import check_match


def _backward_translate(sequence, rule, match_list):
    # Collects all information we have on what was matched, in terms of back-references
    # and classes/features, from what we have in the reflex
    value = {}
    no_nulls = [token for token in rule.post if token.type != "null"]
    for post_entry, token in zip(no_nulls, sequence):
        if post_entry.type == "backref":
            # parse modifier and invert it
            if post_entry.modifier:
                # invert
                # TODO: rename _split_fvalues as it is used externally
                # TODO: have own function?
                modifiers = []
                for mod in maniphono._split_fvalues(post_entry.modifier):
                    if mod[0] == "-":
                        modifiers.append(mod[1:])
                    elif mod[0] == "+":
                        modifiers.append("-" + mod[1:])
                    else:
                        modifiers.append("-" + mod)

                token += modifiers

            value[post_entry.index] = token

    print("SEQ", sequence, len(sequence))
    print("RUL", repr(rule))
    print("NNL", no_nulls, len(no_nulls))
    print("VAL", value)

    no_nulls_copy = []
    for v in no_nulls:
        if v.type != "backref":
            no_nulls_copy.append(v)
        else:
            print("BRX", v.index)
            no_nulls_copy.append(value[v.index])
    print("NNC", no_nulls_copy, len(no_nulls_copy))

    # NOTE: `ante_seq` is here the modified one for reconstruction, not the one in the rule
    ante_seq = []
    for idx, (ante_entry, nnc, match) in enumerate(
        zip(rule.ante, no_nulls_copy, match_list)
    ):
        if ante_entry.type == "choice":
            # TODO: this was already parsed, do we really need to run a .split()?
            # TODO: allow indexing in Choice
            # TODO: comment on -1 due to `all`/`any` etc.
            print("AEE", ante_entry, ante_entry.choices, type(ante_entry))
            print("MTC", match)
            print("NNC", nnc, type(nnc))

            ante_seq.append(nnc)

        #         grapheme = ante_entry.choices[match - 1]
        #         ante_seq.append(
        #             value.get(idx, maniphono.SoundSegment(grapheme))
        #         )  # TODO: correct
        elif ante_entry.type == "set":
            ante_seq.append(
                value.get(idx, maniphono.SoundSegment("t"))
            )  # TODO: correct
        elif ante_entry.type == "segment":
            ante_seq.append(ante_entry.segment)

    # Depending on the type of rule that was applied, the `ante_seq` list
    # might at this point have elements expressing more than one
    # sound and expressing alternatives that need to be computed
    # with a product (e.g., `['#'], ['d'], ['i w', 'j u'], ['d'] ['#']`).
    # This correction is performed by the calling function, also allowing
    # to return a `Sequence` instead of a plain string (so that we also
    # deal with missing boundaries, etc.). We also return the unaltered,
    # original `sequence`, expressing cases where no changes were
    # applied.
    return [
        sequence,
        ante_seq,
    ]


# This method makes a copy of the original AST ante-tokens and applies
# the modifiers from the post sequence; in a way, it "fakes" the
# rule being applied, so that something like "d > @1[+voiceless]"
# is transformed in the equivalent "t > @1".
# TODO: add modifiers, as per previous implementarion
def _carry_backref_modifier(ante_token, post_token):
    # we know post_token is a backref here
    if post_token.modifier:
        if ante_token.type == "segment":  # TODO: only monosonic...
            if len(ante_token.segment.sounds) != 1:
                raise ValueError("only monosonic")

            # make a copy
            x = ante_token.segment.sounds[0]
            return x + post_token.modifier

        elif ante_token.type in ["set", "choice"]:
            # TODO: implement
            return ante_token

    # return non-modified
    return ante_token


# TODO: make sure it works with repeated backreferences, such as "V s > @1 z @1",
# which we *cannot* have mapped only as "V z V"
def backward(post_seq, rule):
    # Compute the `post_ast`, applying modifiers and skipping nulls
    post_ast = [token for token in rule.post if token.type != "empty"]
    print("1>>>", post_ast)
    for idx, token in enumerate(post_ast):
        if token.type != "backref":
            print("  --", idx, token)
        else:
            print(
                "  --", idx, "|", token, token.index, rule.ante, rule.ante[token.index]
            )
            print("   ----", _carry_backref_modifier(rule.ante[token.index], token))

    post_ast = [
        token
        if token.type != "backref"
        else _carry_backref_modifier(rule.ante[token.index], token)
        for token in post_ast
    ]

    # Iterate over the sequence, checking if subsequences match the specified `post`.
    # We operate inside a `while True` loop because we don't allow overlapping
    # matches, and, as such, the `idx` might be updated either with +1 (looking for
    # the next position) or with the match length. While the whole logic could be
    # performed with a more Python list comprehension, for easier conversion to
    # other languages it is better to keep it as dumb loop.
    idx = 0
    ante_seqs = []
    while True:
        # TODO: address comment from original implementation
        sub_seq = post_seq[idx : idx + len(post_ast)]

        match, match_list = check_match(sub_seq, post_ast)
        print("SSEQ", sub_seq)
        print("RULE", rule.post)
        print("PAST", post_ast)
        print("CKM", match, match_list)
        if len(match_list) == 0:
            break

        if match:
            ante_seqs.append(_backward_translate(sub_seq, rule, match_list))
            idx += len(post_ast)
        else:
            # TODO: remove these nested lists if possible
            ante_seqs.append([[post_seq[idx]]])
            idx += 1

        if idx == len(post_seq):
            break

    # TODO: organize and do it properly
    ante_seqs = [
        maniphono.Sequence(
            list(itertools.chain.from_iterable(candidate)), boundaries=True
        )
        for candidate in itertools.product(*ante_seqs)
    ]

    return ante_seqs
