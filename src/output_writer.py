"""
output_writer.py - Write Gherkin .feature files and JSON summaries.
"""

import json
import os
from datetime import date
from typing import List, Dict, Any

from qa_pipeline import UserStory, GherkinScenario

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def write_feature_file(
    feature_name: str,
    stories: List[UserStory],
    scenarios: List[GherkinScenario],
    output_dir: str = OUTPUT_DIR,
) -> str:
    """Write a .feature file in Gherkin syntax."""
    os.makedirs(output_dir, exist_ok=True)

    # Build story lookup for descriptions
    story_map = {s.id: s for s in stories}

    lines = [f"Feature: {feature_name}", ""]

    # Group scenarios by story
    story_scenarios: Dict[str, List[GherkinScenario]] = {}
    for sc in scenarios:
        story_scenarios.setdefault(sc.story_id, []).append(sc)

    for story in stories:
        lines.append(f"  # {story.id}: {story.title}")
        lines.append(f"  # {story.description}")
        lines.append("")
        for sc in story_scenarios.get(story.id, []):
            lines.append(sc.to_gherkin())
            lines.append("")

    content = "\n".join(lines)
    safe_name = feature_name.lower().replace(" ", "_").replace("/", "_")
    filename  = f"{safe_name}_{date.today().isoformat()}.feature"
    out_path  = os.path.join(output_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Output] Feature file saved: {out_path}")
    return out_path


def write_json_report(
    feature_name: str,
    stories: List[UserStory],
    scenarios: List[GherkinScenario],
    output_dir: str = OUTPUT_DIR,
) -> str:
    """Write a structured JSON report."""
    os.makedirs(output_dir, exist_ok=True)

    report = {
        "feature":      feature_name,
        "generated_on": date.today().isoformat(),
        "user_stories": [
            {
                "id":                   s.id,
                "title":                s.title,
                "description":          s.description,
                "acceptance_criteria":  s.acceptance_criteria,
            }
            for s in stories
        ],
        "gherkin_scenarios": [
            {
                "story_id": sc.story_id,
                "title":    sc.title,
                "given":    sc.given,
                "when":     sc.when,
                "then":     sc.then,
            }
            for sc in scenarios
        ],
        "statistics": {
            "total_stories":   len(stories),
            "total_scenarios": len(scenarios),
            "total_criteria":  sum(len(s.acceptance_criteria) for s in stories),
        },
    }

    safe_name = feature_name.lower().replace(" ", "_").replace("/", "_")
    filename  = f"{safe_name}_report_{date.today().isoformat()}.json"
    out_path  = os.path.join(output_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[Output] JSON report saved: {out_path}")
    return out_path
