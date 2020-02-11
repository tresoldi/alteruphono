#!/usr/bin/env python3

"""
test_changers
=============

Tests for the changers in the `alteruphono` package.
"""

# Import third-party libraries
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono
from alteruphono.parser import _tokens2ast

# TODO: could read the phonetic data a single time?


class TestChangers(unittest.TestCase):
    """
    Class for `alteruphono` tests related to changers.
    """

    def test_forward_hardcoded(self):
        reference = {
            ("p > b", "# p a p a #"): ("#", "b", "a", "b", "a", "#"),
            ("S > p / _ V", "t i s e"): ("p", "i", "s", "e"),
            ("t[voiced] > s", "t a d a"): ("t", "a", "s", "a"),
            ("S[voiceless] a > @1[fricative] a", "b a p a t a"): (
                "b",
                "a",
                "ɸ",
                "a",
                "s",
                "a",
            ),
            ("p|t a @1|k > p a t", "t a k"): ("p", "a", "t"),
            ("p|d a > @1{b,d} e", "d a p a"): ("d", "e", "b", "e"),
        }

        # Read phonetic data
        alteruphono.utils.read_phonetic_data()

        # Run tests
        for test, ref in reference.items():
            ast = alteruphono.parse(test[0])
            ante_seq = test[1].split()
            post_seq = alteruphono.forward(ante_seq, ast)
            assert tuple(post_seq) == ref

    def test_backward_hardcoded(self):
        reference = {
            ("p V > b a", "b a r b a"): (
                "b a r b a",
                "b a r p V",
                "p V r b a",
                "p V r p V",
            )
        }

        # Read phonetic data
        alteruphono.utils.read_phonetic_data()

        # Run tests
        for test, ref in reference.items():
            ast = alteruphono.parse(test[0])
            post_seq = test[1].split()
            ante_seqs = alteruphono.backward(post_seq, ast)
            assert tuple(sorted(ante_seqs)) == ref

    def test_forward_resources(self):
        # Read phonetic data
        alteruphono.utils.read_phonetic_data()
        sound_changes = alteruphono.utils.read_sound_changes()

        for change_id, change in sorted(sound_changes.items()):
            ast = alteruphono.parse(change["RULE"])
            test_ante = change["TEST_ANTE"].split()
            test_post = change["TEST_POST"].split()
            post_seq = alteruphono.forward(test_ante, ast)

            if tuple(test_post) != tuple(post_seq):
                print("\nFORWARD")
                print(change_id, change["RULE"])
                print("ANTE", test_ante)
                print("POST", test_post)
                print("MINE", post_seq)

    def test_backward_resources(self):
        # Read phonetic data
        alteruphono.utils.read_phonetic_data()
        sound_changes = alteruphono.utils.read_sound_changes()

        for change_id, change in sorted(sound_changes.items()):
            ast = alteruphono.parse(change["RULE"])
            test_ante = " ".join(change["TEST_ANTE"].split())
            test_post = change["TEST_POST"].split()

            ante_seqs = alteruphono.backward(test_post, ast)

            # TODO: must check sound classes
            if test_ante not in ante_seqs:

                ante_asts = [
                    _tokens2ast(ante_seq.split()) for ante_seq in ante_seqs
                ]
                matches = [
                    alteruphono.check_match(test_ante.split(), ante_ast)
                    for ante_ast in ante_asts
                ]

                if not any(matches):
                    print("\nBACKWARD")
                    print(change_id, change["RULE"])
                    print("ANTE", [test_ante])
                    print("POST", test_post)
                    print("MINE", ante_seqs)
                    for i, a in enumerate(ante_asts):
                        print(i, a)


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangers)
    unittest.TextTestRunner(verbosity=2).run(suite)
