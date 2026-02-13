"""Tests for alteruphono.cli — command-line interface."""

import io
import json

from alteruphono.cli import (
    build_parser,
    cmd_backward,
    cmd_features,
    cmd_forward,
    cmd_systems,
    cmd_validate,
)


def _run_cmd(cmd_func, args_dict, json_mode=False):  # type: ignore[no-untyped-def]
    """Helper to run a CLI command and capture output."""
    import argparse

    ns = argparse.Namespace(**args_dict, json=json_mode)
    out = io.StringIO()
    ret = cmd_func(ns, out=out)
    return ret, out.getvalue()


class TestCLIForward:
    def test_basic(self) -> None:
        ret, output = _run_cmd(cmd_forward, {"rule": "p > b", "sequence": "# a p a #"})
        assert ret == 0
        assert "b" in output

    def test_json(self) -> None:
        ret, output = _run_cmd(
            cmd_forward, {"rule": "p > b", "sequence": "# a p a #"}, json_mode=True
        )
        assert ret == 0
        data = json.loads(output)
        assert data["output"] == "# a b a #"


class TestCLIBackward:
    def test_basic(self) -> None:
        ret, output = _run_cmd(cmd_backward, {"rule": "p > b", "sequence": "# a b a #"})
        assert ret == 0
        assert len(output.strip()) > 0

    def test_json(self) -> None:
        ret, output = _run_cmd(
            cmd_backward, {"rule": "p > b", "sequence": "# a b a #"}, json_mode=True
        )
        assert ret == 0
        data = json.loads(output)
        assert "outputs" in data


class TestCLIFeatures:
    def test_vowel(self) -> None:
        ret, output = _run_cmd(cmd_features, {"grapheme": "a", "system": None})
        assert ret == 0
        assert "vowel" in output

    def test_json(self) -> None:
        ret, output = _run_cmd(
            cmd_features, {"grapheme": "a", "system": None}, json_mode=True
        )
        assert ret == 0
        data = json.loads(output)
        assert "vowel" in data["features"]


class TestCLISystems:
    def test_list(self) -> None:
        ret, output = _run_cmd(cmd_systems, {})
        assert ret == 0
        assert "ipa" in output

    def test_json(self) -> None:
        ret, output = _run_cmd(cmd_systems, {}, json_mode=True)
        assert ret == 0
        data = json.loads(output)
        assert "ipa" in data


class TestCLIValidate:
    def test_valid(self) -> None:
        ret, output = _run_cmd(cmd_validate, {"rule": "p > b"})
        assert ret == 0
        assert "Valid" in output

    def test_invalid(self) -> None:
        ret, output = _run_cmd(cmd_validate, {"rule": "invalid"})
        assert ret == 1

    def test_valid_json(self) -> None:
        ret, output = _run_cmd(cmd_validate, {"rule": "p > b"}, json_mode=True)
        assert ret == 0
        data = json.loads(output)
        assert data["valid"] is True

    def test_invalid_set_arity_json(self) -> None:
        ret, output = _run_cmd(cmd_validate, {"rule": "{p|b} > {f|v} {f|v}"}, json_mode=True)
        assert ret == 1
        data = json.loads(output)
        assert data["valid"] is False
        assert "Set correspondence mismatch" in data["error"]


class TestBuildParser:
    def test_parser_creation(self) -> None:
        parser = build_parser()
        assert parser is not None

    def test_version(self) -> None:
        parser = build_parser()
        import pytest

        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])
