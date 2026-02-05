import os
import tempfile
import unittest

from database.sqlite_service import SQLiteService
from services.validation_service import validate_password, validate_user_id


class AppFeatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = SQLiteService(path=self.tmp.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_user_id_accepts_numeric_or_email(self):
        self.assertEqual(validate_user_id("12345"), "12345")
        self.assertEqual(validate_user_id("Test@Email.com"), "test@email.com")
        with self.assertRaises(ValueError):
            validate_user_id("bad id")

    def test_password_strength(self):
        self.assertEqual(validate_password("Good#123"), "Good#123")
        with self.assertRaises(ValueError):
            validate_password("weakpass")

    def test_registration_and_duplicate_email(self):
        self.db.create_basic_user("9001", "Pass#123A")
        self.db.complete_profile(
            {
                "user_id": "9001",
                "full_name": "Alice Tan",
                "id_no": "ABC12345",
                "telephone": "0123456789",
                "email": "alice@example.com",
                "zone": "Zone A",
                "address": "Street 1",
                "role": "Resident",
            }
        )
        self.db.create_basic_user("9002", "Pass#123A")
        with self.assertRaises(ValueError):
            self.db.complete_profile(
                {
                    "user_id": "9002",
                    "full_name": "Bob Tan",
                    "id_no": "ABC12346",
                    "telephone": "0123456799",
                    "email": "alice@example.com",
                    "zone": "Zone A",
                    "address": "Street 2",
                    "role": "Resident",
                }
            )

    def test_login_attempt_lockout(self):
        self.db.create_basic_user("9010", "Pass#123A")
        for _ in range(4):
            ok, status = self.db.verify_credentials("9010", "wrong")
            self.assertFalse(ok)
            self.assertIn("attempts_left:", status)
        ok, status = self.db.verify_credentials("9010", "wrong")
        self.assertFalse(ok)
        self.assertIn("attempts_left:0", status)
        ok, status = self.db.verify_credentials("9010", "Pass#123A")
        self.assertFalse(ok)
        self.assertEqual(status, "locked")

    def test_points_calculation_updates_user(self):
        self.db.create_basic_user("9020", "Pass#123A")
        self.db.complete_profile(
            {
                "user_id": "9020",
                "full_name": "Carol Lim",
                "id_no": "ABC12347",
                "telephone": "0123456788",
                "email": "carol@example.com",
                "zone": "Zone B",
                "address": "Street 3",
                "role": "Resident",
            }
        )
        points = self.db.create_recycling_log("9020", "plastic", 2.0)
        self.assertEqual(points, 10)
        user = self.db.get_user("9020")
        self.assertEqual(user["total_points"], 10)


if __name__ == "__main__":
    unittest.main()
