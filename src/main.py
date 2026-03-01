"""
main.py - CLI for the AI-Driven QA & Test Case Generator.

Usage:
    # With mock LLM (no API key needed):
    python main.py generate --prd data/prd_samples/auth_system_prd.txt

    # With OpenAI (requires OPENAI_API_KEY):
    python main.py generate --prd data/prd_samples/auth_system_prd.txt --llm openai

    # Specify feature name:
    python main.py generate --prd myfile.txt --feature "Shopping Cart"
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from prd_ingestor import ingest_prd
from qa_pipeline import QAPipeline, MockLLM, OpenAILLM
from output_writer import write_feature_file, write_json_report

SAMPLE_PRD = os.path.join(
    os.path.dirname(__file__), "..", "data", "prd_samples", "auth_system_prd.txt"
)


def main():
    parser = argparse.ArgumentParser(
        description="AI-Driven QA & Test Case Generator"
    )
    sub = parser.add_subparsers(dest="command")

    gen_p = sub.add_parser("generate", help="Generate test cases from a PRD")
    gen_p.add_argument("--prd",     default=SAMPLE_PRD, help="Path to PRD file")
    gen_p.add_argument("--feature", default=None,       help="Feature name override")
    gen_p.add_argument(
        "--llm",
        choices=["mock", "openai"],
        default="mock",
        help="LLM backend to use (default: mock)"
    )
    gen_p.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model name (only used with --llm openai)"
    )

    args = parser.parse_args()

    if args.command == "generate":
        # Select LLM
        if args.llm == "openai":
            llm = OpenAILLM(model=args.model)
            print(f"[Pipeline] Using OpenAI ({args.model})")
        else:
            llm = MockLLM()
            print("[Pipeline] Using MockLLM (offline mode)")

        # Ingest PRD
        print(f"[Pipeline] Reading PRD: {args.prd}")
        prd_text = ingest_prd(args.prd)
        print(f"[Pipeline] PRD length: {len(prd_text)} characters")

        # Determine feature name
        feature_name = args.feature or os.path.splitext(
            os.path.basename(args.prd)
        )[0].replace("_", " ").title()

        # Run pipeline
        print("[Pipeline] Extracting User Stories...")
        pipeline = QAPipeline(llm=llm)
        result   = pipeline.run(prd_text)
        stories  = result["user_stories"]
        scenarios = result["scenarios"]

        print(f"[Pipeline] Found {len(stories)} user stories, "
              f"{len(scenarios)} scenarios")

        # Write outputs
        feat_path = write_feature_file(feature_name, stories, scenarios)
        json_path = write_json_report(feature_name, stories, scenarios)

        print("\n=== GENERATED TEST CASES ===")
        for sc in scenarios:
            print(f"\n{sc.to_gherkin()}")
        print(f"\n[Done] Feature file : {feat_path}")
        print(f"[Done] JSON report  : {json_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
