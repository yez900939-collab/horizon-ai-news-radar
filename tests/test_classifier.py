import unittest

from src.llm.classifier import classify_by_keywords


class ClassifierTests(unittest.TestCase):
    def test_routes_vulnerability_news_to_security_category(self):
        category = classify_by_keywords(
            "Critical RCE vulnerability patched in popular library",
            ["CVE", "exploit"],
        )

        self.assertEqual(category, "漏洞与威胁")

    def test_routes_ai_security_news_to_ai_security_category(self):
        category = classify_by_keywords(
            "New research on LLM prompt injection defenses",
            ["AI security", "jailbreak"],
        )

        self.assertEqual(category, "AI 安全")

    def test_does_not_match_rce_inside_an_ordinary_word(self):
        category = classify_by_keywords(
            "Univé builds an AI-ready workforce",
            [],
        )

        self.assertNotEqual(category, "漏洞与威胁")


if __name__ == "__main__":
    unittest.main()
