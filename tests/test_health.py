import tempfile
import unittest
from pathlib import Path

from create_double.system import health


class HealthTests(unittest.TestCase):
    def test_write_access_ok_creates_and_removes_probe(self):
        with tempfile.TemporaryDirectory() as tempdir:
            ok, detail = health.write_access_ok(Path(tempdir))
            self.assertTrue(ok)
            self.assertTrue(detail.endswith("doubles"))

    def test_format_doctor_report_includes_status_lines(self):
        report = {
            "ok": False,
            "checks": [
                {"name": "Python", "ok": True, "detail": "3.11.0"},
                {"name": "Repo validation", "ok": False, "detail": "missing required path: README.md"},
            ],
            "next_steps": ["python scripts/validate_repo.py"],
        }

        rendered = health.format_doctor_report(report)
        self.assertIn("[OK] Python: 3.11.0", rendered)
        self.assertIn("[WARN] Repo validation: missing required path: README.md", rendered)
        self.assertIn("- python scripts/validate_repo.py", rendered)


if __name__ == "__main__":
    unittest.main()
