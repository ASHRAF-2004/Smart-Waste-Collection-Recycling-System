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

    def test_user_id_accepts_alphanumeric_5_to_10_chars(self):
        self.assertEqual(validate_user_id("abc12"), "abc12")
        self.assertEqual(validate_user_id("A1B2C3D4"), "A1B2C3D4")
        with self.assertRaises(ValueError):
            validate_user_id("1234")
        with self.assertRaises(ValueError):
            validate_user_id("bad id")

    def test_password_strength(self):
        self.assertEqual(validate_password("Good#123"), "Good#123")
        with self.assertRaises(ValueError):
            validate_password("weakpass")

    def test_registration_and_duplicate_email(self):
        self.db.create_basic_user("user901", "Pass#123A")
        self.db.complete_profile(
            {
                "user_id": "user901",
                "full_name": "Alice Tan",
                "id_no": "ABC12345",
                "telephone": "0123456789",
                "email": "alice@example.com",
                "zone": "Zone A",
                "address": "Street 1",
                "role": "Resident",
            }
        )
        self.db.create_basic_user("user902", "Pass#123A")
        with self.assertRaises(ValueError):
            self.db.complete_profile(
                {
                    "user_id": "user902",
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
        self.db.create_basic_user("user910", "Pass#123A")
        for _ in range(4):
            ok, status = self.db.verify_credentials("user910", "wrong")
            self.assertFalse(ok)
            self.assertIn("attempts_left:", status)
        ok, status = self.db.verify_credentials("user910", "wrong")
        self.assertFalse(ok)
        self.assertIn("attempts_left:0", status)
        ok, status = self.db.verify_credentials("user910", "Pass#123A")
        self.assertFalse(ok)
        self.assertEqual(status, "locked")

    def test_admin_user_crud_and_collector_metrics(self):
        self.db.add_user(
            {
                "user_id": "user930",
                "password": "Pass#123A",
                "full_name": "Collector B",
                "role": "WasteCollector",
                "zone": "Zone A",
                "telephone": "0123456781",
                "email": "collectorb@example.com",
                "address": "Road 3",
            }
        )
        self.db.update_user("user930", {"full_name": "Collector Bravo", "zone": "Zone B"})
        updated = self.db.get_user("user930")
        self.assertEqual(updated["full_name"], "Collector Bravo")
        self.assertEqual(updated["zone"], "Zone B")

        requests = self.db.get_collector_requests("collect01")
        self.assertGreaterEqual(len(requests), 1)
        pickup_id = requests[0]["pickup_id"]
        self.db.update_pickup_status("collect01", pickup_id, "COMPLETED", "Done", "evidence.png")
        metrics = self.db.collector_metrics("collect01")
        self.assertGreaterEqual(metrics["completed"], 1)

        self.db.delete_user("user930")
        self.assertIsNone(self.db.get_user("user930"))


if __name__ == "__main__":
    unittest.main()
