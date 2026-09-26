import unittest

from ops_brief import validate_brief


class BriefValidationTests(unittest.TestCase):
    def setUp(self):
        self.brief = {
            "reported_facts": ["First response takes about 45 seconds."],
            "unknowns": ["GPU placement has not been checked."],
            "next_checks": ["Inspect the loaded model and runtime state."],
            "priority": "normal",
            "handoff_note": "Capture model-load timing before changing settings.",
        }

    def test_accepts_complete_brief(self):
        self.assertEqual(validate_brief(self.brief), self.brief)

    def test_rejects_invented_field(self):
        self.brief["root_cause"] = "Unknown"
        with self.assertRaises(ValueError):
            validate_brief(self.brief)

    def test_rejects_empty_checks(self):
        self.brief["next_checks"] = []
        with self.assertRaises(ValueError):
            validate_brief(self.brief)

    def test_rejects_unsupported_priority(self):
        self.brief["priority"] = "critical"
        with self.assertRaises(ValueError):
            validate_brief(self.brief)


if __name__ == "__main__":
    unittest.main()

