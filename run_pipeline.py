from __future__ import annotations

import argparse
from pathlib import Path

from courseweaver.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CourseWeaver MVP pipeline on a PDF lecture.")
    parser.add_argument("pdf", type=Path, help="Path to the source PDF")
    parser.add_argument("--out", type=Path, default=None, help="Output directory, defaults to output/<pdf-name>")
    parser.add_argument("--project-id", default=None, help="Stable project id used in exported metadata")
    parser.add_argument("--use-llm", action="store_true", help="Use an LLM provider to rewrite note chunks after CourseIR planning")
    parser.add_argument(
        "--llm-provider",
        choices=["deepseek", "kimi"],
        default="deepseek",
        help="LLM provider used when --use-llm is enabled",
    )
    parser.add_argument("--llm-model", default=None, help="Provider model name, e.g. deepseek-v4-pro or kimi-k2.6")
    parser.add_argument("--deepseek-model", default=None, help="Deprecated alias for --llm-model when provider is deepseek")
    parser.add_argument(
        "--deepseek-thinking",
        choices=["enabled", "disabled"],
        default="disabled",
        help="DeepSeek thinking mode switch for note rewriting",
    )
    args = parser.parse_args()

    project = run_pipeline(
        args.pdf,
        args.out,
        args.project_id,
        use_llm=args.use_llm,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model or args.deepseek_model,
        deepseek_thinking=args.deepseek_thinking,
    )
    output_dir = args.out or Path("output") / project.project_id

    print(f"CourseWeaver MVP finished: {project.project_id}")
    print(f"Pages: {len(project.pages)}")
    print(f"Blocks: {len(project.blocks)}")
    print(f"Knowledge units: {len(project.knowledge_units)}")
    print(f"Covered blocks: {project.coverage_summary.get('covered', 0)}")
    print(f"Missing blocks: {project.coverage_summary.get('missing', 0)}")
    model_label = args.llm_model or args.deepseek_model or ("kimi-k2.6" if args.llm_provider == "kimi" else "deepseek-v4-pro")
    print(f"LLM rewrite: {args.llm_provider} {model_label}" if args.use_llm else "LLM rewrite: disabled")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
