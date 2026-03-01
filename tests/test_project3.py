"""
test_project3.py - Unit tests for AI-Driven QA & Test Case Generator
"""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prd_ingestor import ingest_prd
from qa_pipeline import QAPipeline, MockLLM, UserStory, GherkinScenario
from output_writer import write_feature_file, write_json_report


SAMPLE_PRD_TEXT = """
# Test PRD: Shopping Cart Feature

## Feature 1: Add to Cart
Users should be able to add products to their shopping cart.
Requirements:
- Users can add any in-stock product to cart.
- Cart shows item count badge in header.
- Out-of-stock items cannot be added.

## Feature 2: Checkout
Users should be able to purchase items in cart.
Requirements:
- Users must be logged in to checkout.
- Payment must be processed securely.
- Confirmation email sent after successful purchase.
"""


class TestPRDIngestor(unittest.TestCase):
    def test_read_txt(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(SAMPLE_PRD_TEXT)
        text = ingest_prd(path)
        os.unlink(path)
        self.assertIn("Shopping Cart", text)

    def test_read_md(self):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w") as f:
            f.write(SAMPLE_PRD_TEXT)
        text = ingest_prd(path)
        os.unlink(path)
        self.assertGreater(len(text), 0)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            ingest_prd("/no/such/file.txt")

    def test_unsupported_type_raises(self):
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        with self.assertRaises(ValueError):
            ingest_prd(path)
        os.unlink(path)


class TestQAPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = QAPipeline(llm=MockLLM())

    def test_extract_stories(self):
        stories = self.pipeline.extract_user_stories(SAMPLE_PRD_TEXT)
        self.assertIsInstance(stories, list)
        self.assertGreater(len(stories), 0)
        self.assertIsInstance(stories[0], UserStory)
        self.assertTrue(stories[0].id.startswith("US-"))

    def test_stories_have_acceptance_criteria(self):
        stories = self.pipeline.extract_user_stories(SAMPLE_PRD_TEXT)
        for story in stories:
            self.assertIsInstance(story.acceptance_criteria, list)
            self.assertGreater(len(story.acceptance_criteria), 0)

    def test_generate_gherkin(self):
        stories   = self.pipeline.extract_user_stories(SAMPLE_PRD_TEXT)
        scenarios = self.pipeline.generate_gherkin(stories)
        self.assertIsInstance(scenarios, list)
        self.assertGreater(len(scenarios), 0)
        self.assertIsInstance(scenarios[0], GherkinScenario)

    def test_gherkin_has_steps(self):
        stories   = self.pipeline.extract_user_stories(SAMPLE_PRD_TEXT)
        scenarios = self.pipeline.generate_gherkin(stories)
        for sc in scenarios:
            # At minimum given or when should be present
            self.assertTrue(len(sc.given) + len(sc.when) + len(sc.then) > 0)

    def test_full_pipeline_run(self):
        result = self.pipeline.run(SAMPLE_PRD_TEXT)
        self.assertIn("user_stories", result)
        self.assertIn("scenarios", result)

    def test_gherkin_to_string(self):
        sc = GherkinScenario(
            story_id="US-001",
            title="Successful login",
            given=["the user is on the login page"],
            when=["the user enters valid credentials"],
            then=["the user is redirected to the dashboard"],
        )
        text = sc.to_gherkin()
        self.assertIn("Scenario: Successful login", text)
        self.assertIn("Given", text)
        self.assertIn("When", text)
        self.assertIn("Then", text)

    def test_invalid_json_raises(self):
        class BadLLM:
            def complete(self, s, u):
                return "this is not json at all"
        with self.assertRaises(ValueError):
            QAPipeline(llm=BadLLM()).extract_user_stories("some PRD")


class TestOutputWriter(unittest.TestCase):
    def setUp(self):
        pipeline = QAPipeline(llm=MockLLM())
        result = pipeline.run(SAMPLE_PRD_TEXT)
        self.stories   = result["user_stories"]
        self.scenarios = result["scenarios"]

    def test_write_feature_file(self):
        with tempfile.TemporaryDirectory() as out_dir:
            path = write_feature_file("Test Feature", self.stories,
                                      self.scenarios, out_dir)
            self.assertTrue(os.path.isfile(path))
            self.assertTrue(path.endswith(".feature"))
            content = open(path).read()
            self.assertIn("Feature: Test Feature", content)

    def test_write_json_report(self):
        with tempfile.TemporaryDirectory() as out_dir:
            path = write_json_report("Test Feature", self.stories,
                                     self.scenarios, out_dir)
            self.assertTrue(os.path.isfile(path))
            data = json.loads(open(path).read())
            self.assertIn("user_stories", data)
            self.assertIn("statistics", data)
            self.assertEqual(data["statistics"]["total_stories"], len(self.stories))


if __name__ == "__main__":
    unittest.main(verbosity=2)
