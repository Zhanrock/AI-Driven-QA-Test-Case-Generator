# 🤖 AI-Driven QA & Test Case Generator

A Generative AI pipeline that bridges the gap between business requirements and executable technical tests by automatically extracting User Stories and generating Gherkin BDD test scripts from Product Requirement Documents (PRDs).

## Overview

This tool ingests PRDs in PDF, DOCX, or text format, uses Chain-of-Thought (CoT) prompting to extract User Stories and Acceptance Criteria, and then generates structured Gherkin (Cucumber) test scripts aligned with those requirements.

### Key Features

- **Multi-format PRD ingestion**: `.txt`, `.md`, `.pdf`, `.docx`
- **Chain-of-Thought prompting** for accurate requirement extraction
- **Dual LLM support**: OpenAI API (production) or MockLLM (offline/testing)
- **Gherkin `.feature` file generation** with proper BDD syntax
- **JSON report** with full traceability from requirement → user story → test scenario
- **Extensible architecture**: plug in any LLM backend

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| PRD Parsing     | Python, pdfplumber/PyPDF2, docx     |
| LLM Orchestration | OpenAI API / MockLLM (offline)   |
| Prompt Strategy | Chain-of-Thought (CoT)              |
| Test Output     | Gherkin (Cucumber) `.feature` files |
| Data Exchange   | JSON                                |
| Testing         | unittest                            |

## Project Structure

```
project3/
├── src/
│   ├── prd_ingestor.py   # PRD file reading (txt/md/pdf/docx)
│   ├── qa_pipeline.py    # LLM pipeline: stories + Gherkin generation
│   ├── output_writer.py  # .feature file & JSON report writer
│   └── main.py           # CLI entry point
├── data/
│   └── prd_samples/
│       └── auth_system_prd.txt
├── outputs/              # Generated .feature files & JSON reports
├── tests/
│   └── test_project3.py
└── requirements.txt
```

## Installation

```bash
cd project3
pip install -r requirements.txt

# For OpenAI support:
pip install openai

# For PDF support:
pip install pdfplumber

# For DOCX support:
pip install python-docx
```

## Usage

```bash
# Offline mode (MockLLM — no API key required):
cd src
python main.py generate --prd data/prd_samples/auth_system_prd.txt

# With OpenAI (requires OPENAI_API_KEY environment variable):
export OPENAI_API_KEY=sk-...
python main.py generate --prd data/prd_samples/auth_system_prd.txt --llm openai

# Specify a custom feature name:
python main.py generate --prd my_prd.pdf --feature "Payment Processing" --llm openai
```

## Output Example

### Gherkin `.feature` file
```gherkin
Feature: User Authentication System

  # US-001: User Login
  # As a registered user, I want to log in, so that I can access my account.

  Scenario: Successful login
    Given the user is on the login page
    When the user enters valid email and password
    Then the user is redirected to the dashboard

  Scenario: Failed login after 5 attempts
    Given the user has failed login 4 times
    When the user enters invalid credentials again
    Then the account is locked for 15 minutes
```

### JSON Report
```json
{
  "feature": "User Authentication System",
  "statistics": {
    "total_stories": 4,
    "total_scenarios": 8,
    "total_criteria": 16
  },
  "user_stories": [...],
  "gherkin_scenarios": [...]
}
```

## LLM Backends

### MockLLM (Default — No API key)
Produces deterministic output for testing and demonstration. Ideal for CI/CD pipelines.

### OpenAILLM
Uses GPT-4o (configurable) via the OpenAI Chat Completions API. Produces context-aware, PRD-specific test cases.

### Custom LLM
Implement any backend with a `complete(system_prompt, user_prompt) -> str` method:
```python
class MyLLM:
    def complete(self, system_prompt, user_prompt):
        # call your model
        return json_string

pipeline = QAPipeline(llm=MyLLM())
```

## Running Tests

```bash
python tests/test_project3.py
```

Expected: **13 tests, 0 failures**

## Impact

- Reduces manual test case creation effort by up to 80%
- Ensures 100% traceability between business requirements and test scenarios
- Accelerates QA onboarding with auto-generated Gherkin scripts
- Supports any LLM backend via pluggable architecture
