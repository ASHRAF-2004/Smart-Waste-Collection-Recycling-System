import os
import tempfile
import unittest
from datetime import datetime, timedelta

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

    def test_user_id_rules(self):
        self.assertEqual(validate_user_id("A12345"), "A12345")
        self.assertEqual(validate_user_id("Ashraf01"), "Ashraf01")
        for bad in ("123456", "ab 1234", "abc", "A1234567890123"):
            with self.assertRaises(ValueError):
                validate_user_id(bad)

    def test_password_rules(self):
        self.assertEqual(validate_password("StrongPass1"), "StrongPass1")
        with self.assertRaises(ValueError):
            validate_password("password")
        with self.assertRaises(ValueError):
            validate_password("weakpass")

    def test_registration_and_duplicate(self):
        self.db.create_basic_user("Resident1", "StrongPass1")
        self.db.complete_profile(
            {
                "user_id": "Resident1",
                "full_name": "Alice Tan",
                "id_no": "ABC12345",
                "telephone": "+60123456789",
                "email": "alice@example.com",
                "zone": "Zone A",
                "address": "Street 1",
            }
        )
        self.db.create_basic_user("Resident2", "StrongPass1")
        with self.assertRaises(ValueError):
            self.db.complete_profile(
                {
                    "user_id": "Resident2",
                    "full_name": "Bob Tan",
                    "id_no": "ABC12346",
                    "telephone": "+60123456788",
                    "email": "alice@example.com",
                    "zone": "Zone A",
                    "address": "Street 2",
                }
            )

    def test_pickup_flow_and_notifications(self):
        self.db.create_basic_user("Resident3", "StrongPass1")
        self.db.complete_profile({"user_id": "Resident3", "full_name": "Res Three", "id_no": "ID123456", "telephone": "+60121112222", "email": "r3@example.com", "zone": "Zone A", "address": "A Road"})
        dt = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        self.db.create_pickup_request("Resident3", dt)
        req = self.db.list_resident_pickups("Resident3")[0]
        self.db.update_pickup_status("Collect1", req["pickup_id"], "IN_PROGRESS", "Started")
        self.db.update_pickup_status("Collect1", req["pickup_id"], "COMPLETED", "Done")
        notes = self.db.get_notifications("Resident3")
        self.assertGreaterEqual(len(notes), 2)


if __name__ == "__main__":
    unittest.main()
