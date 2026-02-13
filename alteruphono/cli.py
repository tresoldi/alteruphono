"""Command-line interface for alteruphono."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TextIO

from alteruphono import __version__
from alteruphono.backward import backward
from alteruphono.features import list_systems, sound
from alteruphono.forward import forward
from alteruphono.parser import parse_rule, parse_sequence


def _format_sequence(seq: tuple[object, ...]) -> str:
    return " ".join(str(e) for e in seq)


def cmd_forward(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    """Apply a rule forward."""
    rule = parse_rule(args.rule)
    seq = parse_sequence(args.sequence)
    result = forward(seq, rule)

    if args.json:
        data = {
            "rule": args.rule,
            "input": _format_sequence(seq),
            "output": _format_sequence(result),
        }
        out.write(json.dumps(data, ensure_ascii=False) + "\n")
    else:
        out.write(_format_sequence(result) + "\n")
    return 0


def cmd_backward(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    """Reconstruct possible proto-forms."""
    rule = parse_rule(args.rule)
    seq = parse_sequence(args.sequence)
    results = backward(seq, rule)

    if args.json:
        data = {
            "rule": args.rule,
            "input": _format_sequence(seq),
            "outputs": [_format_sequence(r) for r in results],
        }
        out.write(json.dumps(data, ensure_ascii=False) + "\n")
    else:
        for r in results:
            out.write(_format_sequence(r) + "\n")
    return 0


def cmd_features(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    """Show features for a grapheme."""
    snd = sound(args.grapheme, args.system)

    if args.json:
        data = {
            "grapheme": snd.grapheme,
            "features": sorted(snd.features),
            "partial": snd.partial,
        }
        out.write(json.dumps(data, ensure_ascii=False) + "\n")
    else:
        out.write(f"Grapheme: {snd.grapheme}\n")
        out.write(f"Partial: {snd.partial}\n")
        out.write(f"Features: {', '.join(sorted(snd.features)) or '(none)'}\n")
    return 0


def cmd_systems(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    """List available feature systems."""
    systems = list_systems()

    if args.json:
        out.write(json.dumps(systems) + "\n")
    else:
        for s in systems:
            out.write(s + "\n")
    return 0


def cmd_validate(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    """Validate a sound change rule."""
    try:
        rule = parse_rule(args.rule)
        if args.json:
            data = {
                "rule": args.rule,
                "valid": True,
                "ante_tokens": len(rule.ante),
                "post_tokens": len(rule.post),
            }
            out.write(json.dumps(data, ensure_ascii=False) + "\n")
        else:
            out.write(f"Valid rule: {args.rule}\n")
            out.write(f"Ante tokens: {len(rule.ante)}\n")
            out.write(f"Post tokens: {len(rule.post)}\n")
        return 0
    except ValueError as e:
        if args.json:
            out.write(json.dumps({"rule": args.rule, "valid": False, "error": str(e)}) + "\n")
        else:
            out.write(f"Invalid rule: {e}\n")
        return 1


def cmd_apply_file(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    """Apply rules from a file to a sequence."""
    seq = parse_sequence(args.sequence)

    with open(args.rules_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Support TSV format (take RULE column or first column)
            parts = line.split("\t")
            rule_str = parts[1] if len(parts) >= 2 else parts[0]

            try:
                rule = parse_rule(rule_str)
                seq = forward(seq, rule)
            except ValueError:
                continue

    if args.json:
        data = {"output": _format_sequence(seq)}
        out.write(json.dumps(data, ensure_ascii=False) + "\n")
    else:
        out.write(_format_sequence(seq) + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="alteruphono",
        description="AlteruPhono — Historical linguistics sound change library",
    )
    parser.add_argument("--version", action="version", version=f"alteruphono {__version__}")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # forward
    p_fwd = subparsers.add_parser("forward", help="Apply a rule forward")
    p_fwd.add_argument("rule", help="Sound change rule (e.g., 'p > b / V _ V')")
    p_fwd.add_argument("sequence", help="Input sequence (e.g., '# a p a #')")

    # backward
    p_bwd = subparsers.add_parser("backward", help="Reconstruct proto-forms")
    p_bwd.add_argument("rule", help="Sound change rule")
    p_bwd.add_argument("sequence", help="Daughter sequence")

    # features
    p_feat = subparsers.add_parser("features", help="Show features for a grapheme")
    p_feat.add_argument("grapheme", help="Grapheme to look up")
    p_feat.add_argument("--system", default=None, help="Feature system name")

    # systems
    subparsers.add_parser("systems", help="List available feature systems")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate a rule")
    p_val.add_argument("rule", help="Sound change rule to validate")

    # apply-file
    p_af = subparsers.add_parser("apply-file", help="Apply rules from a file")
    p_af.add_argument("rules_file", help="Path to rules file (TSV or plain text)")
    p_af.add_argument("sequence", help="Input sequence")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "forward": cmd_forward,
        "backward": cmd_backward,
        "features": cmd_features,
        "systems": cmd_systems,
        "validate": cmd_validate,
        "apply-file": cmd_apply_file,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)
