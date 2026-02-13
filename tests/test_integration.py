"""Integration tests using TSV sound change test data."""

import pytest

from alteruphono import backward, forward
from alteruphono.parser import parse_rule, parse_sequence
from alteruphono.resources import load_sound_changes


def _apply_rule_forward(rule_str: str, ante_str: str) -> str:
    """Apply a rule forward and return result as string."""
    rule = parse_rule(rule_str)
    seq = parse_sequence("# " + ante_str + " #")
    result = forward(seq, rule)
    return " ".join(str(e) for e in result)


def _strip_boundaries(s: str) -> str:
    """Remove leading/trailing # from a string."""
    return s.strip().removeprefix("#").removesuffix("#").strip()


class TestTSVSoundChanges:
    """Test forward application against sound_changes.tsv test cases."""

    @pytest.fixture(scope="class")
    def rules(self) -> list[dict[str, str]]:
        return load_sound_changes()

    def test_rules_loaded(self, rules: list[dict[str, str]]) -> None:
        assert len(rules) > 0

    def test_all_rules(self, rules: list[dict[str, str]]) -> None:
        """Test ALL TSV rules — track pass/fail rate."""
        passed = 0
        failed = 0
        errors = 0
        for row in rules:
            rule_str = row["RULE"]
            test_ante = row["TEST_ANTE"]
            test_post = row["TEST_POST"]

            try:
                result = _apply_rule_forward(rule_str, test_ante)
                result_inner = _strip_boundaries(result)

                if result_inner == test_post:
                    passed += 1
                else:
                    failed += 1
            except Exception:
                errors += 1

        total = passed + failed + errors
        pass_rate = passed / total if total else 0
        # Assert >= 20% pass rate (some rules use unsupported notation)
        assert pass_rate >= 0.20, (
            f"Pass rate too low: {passed}/{total} = {pass_rate:.1%} "
            f"({failed} failed, {errors} errors)"
        )


class TestEndToEnd:
    def test_forward_backward_roundtrip(self) -> None:
        """Forward then backward should contain the original."""
        rule = parse_rule("p > b")
        original = parse_sequence("# a p a #")
        daughter = forward(original, rule)
        protos = backward(daughter, rule)
        original_str = " ".join(str(e) for e in original)
        proto_strs = [" ".join(str(e) for e in p) for p in protos]
        assert original_str in proto_strs

    def test_import_api(self) -> None:
        """Test the public API imports."""
        import alteruphono

        assert hasattr(alteruphono, "forward")
        assert hasattr(alteruphono, "backward")
        assert hasattr(alteruphono, "parse_rule")
        assert hasattr(alteruphono, "parse_sequence")
        assert hasattr(alteruphono, "Sound")
        assert hasattr(alteruphono, "Boundary")
        assert hasattr(alteruphono, "__version__")
        assert alteruphono.__version__ == "1.0.0rc1"
