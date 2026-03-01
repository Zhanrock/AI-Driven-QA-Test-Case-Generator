"""
qa_pipeline.py - Chain-of-Thought LLM pipeline that extracts User Stories,
                 Acceptance Criteria, and generates Gherkin test scripts.

Supports OpenAI API (real) and a Mock LLM (for offline/testing use).
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class UserStory:
    id: str
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class GherkinScenario:
    story_id: str
    title: str
    given: List[str] = field(default_factory=list)
    when: List[str] = field(default_factory=list)
    then: List[str] = field(default_factory=list)

    def to_gherkin(self) -> str:
        lines = [f"  Scenario: {self.title}"]
        for g in self.given:
            lines.append(f"    Given {g}")
        for w in self.when:
            lines.append(f"    When {w}")
        for t in self.then:
            lines.append(f"    Then {t}")
        return "\n".join(lines)


class MockLLM:
    """Offline mock that produces deterministic structured output for testing."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if "scenarios" in system_prompt.lower() or "gherkin" in system_prompt.lower():
            return json.dumps({
                "scenarios": [
                    {
                        "story_id": "US-001",
                        "title": "Successful operation",
                        "given": ["the user is on the main page"],
                        "when": ["the user performs the primary action"],
                        "then": ["the system responds successfully"]
                    },
                    {
                        "story_id": "US-002",
                        "title": "Failed operation handling",
                        "given": ["the user is on the main page"],
                        "when": ["the user enters invalid input"],
                        "then": ["an error message is displayed"]
                    }
                ]
            })

        feature_match = re.search(r"feature[:\s]+([^\n]+)", user_prompt, re.IGNORECASE)
        feature = feature_match.group(1).strip() if feature_match else "User Login"

        return json.dumps({
            "user_stories": [
                {
                    "id": "US-001",
                    "title": f"Basic {feature}",
                    "description": f"As a registered user, I want to {feature.lower()}, so that I can access the system.",
                    "acceptance_criteria": [
                        "System validates credentials against the database",
                        "User is redirected to dashboard on success",
                        "Error message displayed on failure"
                    ]
                },
                {
                    "id": "US-002",
                    "title": f"Failed {feature} Handling",
                    "description": f"As a user, I want clear feedback on failed {feature.lower()}, so that I can correct my inputs.",
                    "acceptance_criteria": [
                        "Error message is displayed after 3 failed attempts",
                        "Account is locked after 5 consecutive failures",
                        "Lockout duration is 15 minutes"
                    ]
                }
            ]
        })


class OpenAILLM:
    """Calls the OpenAI Chat Completion API. Requires OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it as an environment variable."
            )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content


SYSTEM_EXTRACT_STORIES = """
You are a senior QA engineer with expertise in requirements analysis.
Extract all User Stories and their Acceptance Criteria from the provided PRD.

Respond ONLY with valid JSON (no markdown fences) in this exact structure:
{
  "user_stories": [
    {
      "id": "US-001",
      "title": "...",
      "description": "As a <role>, I want <goal>, so that <benefit>",
      "acceptance_criteria": ["...", "..."]
    }
  ]
}

Chain-of-Thought instructions:
1. Read the PRD carefully and identify all distinct features or requirements.
2. For each feature, formulate a User Story in the As/Want/So format.
3. Derive clear, testable Acceptance Criteria from the requirements.
4. Assign sequential IDs (US-001, US-002, ...).
"""

SYSTEM_GENERATE_GHERKIN = """
You are a QA automation engineer. Convert User Stories with Acceptance Criteria
into Gherkin BDD test scenarios.

Respond ONLY with valid JSON (no markdown fences) in this structure:
{
  "scenarios": [
    {
      "story_id": "US-001",
      "title": "...",
      "given": ["..."],
      "when": ["..."],
      "then": ["..."]
    }
  ]
}

Each Acceptance Criterion should become at least one Gherkin scenario.
Write concise, actionable Given/When/Then steps.
"""


class QAPipeline:
    """Orchestrates: PRD text -> User Stories -> Gherkin test scripts."""

    def __init__(self, llm=None):
        self.llm = llm or MockLLM()

    def extract_user_stories(self, prd_text: str) -> List[UserStory]:
        prompt = f"Extract all User Stories from this PRD:\n\n{prd_text}"
        raw = self.llm.complete(SYSTEM_EXTRACT_STORIES, prompt)
        return self._parse_stories(raw)

    def generate_gherkin(self, stories: List[UserStory]) -> List[GherkinScenario]:
        stories_json = json.dumps(
            [{"id": s.id, "title": s.title, "description": s.description,
              "acceptance_criteria": s.acceptance_criteria}
             for s in stories],
            indent=2
        )
        prompt = f"Generate Gherkin scenarios for these User Stories:\n\n{stories_json}"
        raw = self.llm.complete(SYSTEM_GENERATE_GHERKIN, prompt)
        return self._parse_scenarios(raw)

    def run(self, prd_text: str) -> Dict[str, Any]:
        stories = self.extract_user_stories(prd_text)
        scenarios = self.generate_gherkin(stories)
        return {"user_stories": stories, "scenarios": scenarios}

    def _parse_stories(self, raw: str) -> List[UserStory]:
        data = self._safe_json(raw)
        stories = []
        for item in data.get("user_stories", []):
            stories.append(UserStory(
                id=item.get("id", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                acceptance_criteria=item.get("acceptance_criteria", []),
            ))
        return stories

    def _parse_scenarios(self, raw: str) -> List[GherkinScenario]:
        data = self._safe_json(raw)
        scenarios = []
        for item in data.get("scenarios", []):
            scenarios.append(GherkinScenario(
                story_id=item.get("story_id", ""),
                title=item.get("title", ""),
                given=item.get("given", []),
                when=item.get("when", []),
                then=item.get("then", []),
            ))
        return scenarios

    @staticmethod
    def _safe_json(text: str) -> Dict:
        text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\nRaw:\n{text[:300]}")
