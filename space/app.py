"""Minimal Hugging Face Space UI for AlteruPhono."""

from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from alteruphono import backward, forward, parse_rule, parse_sequence

DOC_FILES = {
    "Comprehensive Guide": "guide.md",
}
DOCS_DIR = Path(__file__).resolve().parent / "docs"
EXAMPLES: dict[str, dict[str, str]] = {
    "Basic • Attested • Intervocalic voicing (Romance-type)": {
        "rule": "t > d / V _ V",
        "proto": "# p a t a #\n# m a t e #",
        "daughter": "# p a d a #\n# m a d e #",
        "note": "Attested in many Romance developments as intervocalic lenition/voicing.",
    },
    "Basic • Attested • Final devoicing (German/Dutch-type)": {
        "rule": "b > p / _ #",
        "proto": "# a b #\n# a b a #",
        "daughter": "# a p #\n# a b a #",
        "note": "Attested in German, Dutch, and other languages with word-final obstruent devoicing.",
    },
    "Intermediate • Attested • Rhotacism (Latin-type)": {
        "rule": "s > r / V _ V",
        "proto": "# a s a #\n# o s o #",
        "daughter": "# a r a #\n# o r o #",
        "note": "Intervocalic rhotacism is classically attested in historical Latin developments.",
    },
    "Intermediate • Attested • Nasal place assimilation": {
        "rule": "n > m / _ p|b",
        "proto": "# i n p u t #\n# i n b a #",
        "daughter": "# i m p u t #\n# i m b a #",
        "note": "Common regressive place assimilation before bilabials.",
    },
    "Advanced • Proposed • Grimm's Law step": {
        "rule": "p > f",
        "proto": "# p a t e r #\n# p o d #",
        "daughter": "# f a t e r #\n# f o d #",
        "note": "Classic comparative reconstruction component (proposed systematic correspondence).",
    },
    "Advanced • Attested • Word-final cluster simplification": {
        "rule": "C+ > :null: / _ #",
        "proto": "# a s t #\n# i n t #",
        "daughter": "# a #\n# i #",
        "note": "Attested in many languages/dialects with coda-cluster reduction.",
    },
}


def _seq_to_str(seq: tuple[object, ...]) -> str:
    return " ".join(str(e) for e in seq)


def run_forward(rule_text: str, sequence_text: str, as_json: bool) -> str:
    inputs = [line.strip() for line in sequence_text.splitlines() if line.strip()]
    if not inputs:
        return "Error: provide at least one input sequence (one per line)."

    try:
        rule = parse_rule(rule_text)
        results: list[dict[str, str]] = []
        for sequence_line in inputs:
            seq = parse_sequence(sequence_line)
            out = forward(seq, rule)
            out_str = _seq_to_str(out)
            results.append({"input": sequence_line, "output": out_str})
        if not as_json:
            return "\n".join(f"{row['input']} -> {row['output']}" for row in results)
        return json.dumps(
            {
                "mode": "forward",
                "rule": rule_text,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as exc:  # pragma: no cover - UI guardrail
        return f"Error: {exc}"


def run_backward(rule_text: str, sequence_text: str, as_json: bool) -> str:
    inputs = [line.strip() for line in sequence_text.splitlines() if line.strip()]
    if not inputs:
        return "Error: provide at least one daughter sequence (one per line)."

    try:
        rule = parse_rule(rule_text)
        results: list[dict[str, object]] = []
        for sequence_line in inputs:
            seq = parse_sequence(sequence_line)
            outs = backward(seq, rule)
            out_strs = [_seq_to_str(candidate) for candidate in outs]
            results.append({"input": sequence_line, "candidates": out_strs})
        if not as_json:
            blocks = []
            for row in results:
                lines = [f"Input: {row['input']}"]
                lines.extend(f"  - {candidate}" for candidate in row["candidates"])
                blocks.append("\n".join(lines))
            return "\n\n".join(blocks)
        return json.dumps(
            {
                "mode": "backward",
                "rule": rule_text,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as exc:  # pragma: no cover - UI guardrail
        return f"Error: {exc}"


def run_validate(rule_text: str, as_json: bool) -> str:
    try:
        rule = parse_rule(rule_text)
        if not as_json:
            return (
                f"Valid rule: {rule.source}\n"
                f"Ante tokens: {len(rule.ante)}\n"
                f"Post tokens: {len(rule.post)}"
            )
        return json.dumps(
            {
                "mode": "validate",
                "rule": rule.source,
                "ante_tokens": len(rule.ante),
                "post_tokens": len(rule.post),
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as exc:  # pragma: no cover - UI guardrail
        return f"Error: {exc}"


def load_doc(doc_name: str) -> str:
    filename = DOC_FILES.get(doc_name)
    if filename is None:
        return "Error: unknown document."
    path = DOCS_DIR / filename
    if not path.exists():
        return f"Error: missing documentation file: {filename}"
    return path.read_text(encoding="utf-8")


def apply_example_forward(example_name: str) -> tuple[str, str, str]:
    ex = EXAMPLES[example_name]
    return ex["rule"], ex["proto"], ex["note"]


def apply_example_backward(example_name: str) -> tuple[str, str, str]:
    ex = EXAMPLES[example_name]
    return ex["rule"], ex["daughter"], ex["note"]


with gr.Blocks(title="AlteruPhono Demo") as demo:
    gr.Markdown(
        """
        # AlteruPhono Demo
        Minimal online interface for:
        - `forward`
        - `backward`
        - `validate`
        """
    )

    with gr.Tab("Forward"):
        f_example = gr.Dropdown(
            label="Example set (complexity + status)",
            choices=list(EXAMPLES.keys()),
            value=list(EXAMPLES.keys())[0],
        )
        f_rule = gr.Textbox(label="Rule", value="p > b / V _ V")
        f_seq = gr.Textbox(
            label="Input sequences (one per line)",
            value="# a p a #\n# a t a #",
            lines=5,
        )
        f_note = gr.Markdown("_Select an example to auto-fill fields._")
        f_json = gr.Checkbox(label="JSON output", value=False)
        f_run = gr.Button("Run forward", variant="primary")
        f_out = gr.Textbox(label="Output", lines=8)
        f_example.change(
            apply_example_forward,
            inputs=f_example,
            outputs=[f_rule, f_seq, f_note],
        )
        f_run.click(run_forward, inputs=[f_rule, f_seq, f_json], outputs=f_out)

    with gr.Tab("Backward"):
        b_example = gr.Dropdown(
            label="Example set (complexity + status)",
            choices=list(EXAMPLES.keys()),
            value=list(EXAMPLES.keys())[0],
        )
        b_rule = gr.Textbox(label="Rule", value="p > b")
        b_seq = gr.Textbox(
            label="Daughter sequences (one per line)",
            value="# a b a #\n# a d a #",
            lines=5,
        )
        b_note = gr.Markdown("_Select an example to auto-fill fields._")
        b_json = gr.Checkbox(label="JSON output", value=False)
        b_run = gr.Button("Run backward", variant="primary")
        b_out = gr.Textbox(label="Candidates", lines=10)
        b_example.change(
            apply_example_backward,
            inputs=b_example,
            outputs=[b_rule, b_seq, b_note],
        )
        b_run.click(run_backward, inputs=[b_rule, b_seq, b_json], outputs=b_out)

    with gr.Tab("Validate"):
        v_rule = gr.Textbox(label="Rule", value="p > b / V _ V")
        v_json = gr.Checkbox(label="JSON output", value=False)
        v_run = gr.Button("Validate rule", variant="primary")
        v_out = gr.Textbox(label="Validation", lines=6)
        v_run.click(run_validate, inputs=[v_rule, v_json], outputs=v_out)

    with gr.Tab("Documentation"):
        d_name = "Comprehensive Guide"
        gr.Markdown(load_doc(d_name))


if __name__ == "__main__":
    demo.launch()
