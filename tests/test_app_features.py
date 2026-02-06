import os
import tempfile
import unittest
from datetime import datetime, timedelta

from database.sqlite_service import SQLiteService
from services.validation_service import validate_password, validate_pickup_datetime, validate_user_id


class AppFeatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = SQLiteService(path=self.tmp.name)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_user_id_rules(self):
        self.assertEqual(validate_user_id("User_01"), "User_01")
        with self.assertRaises(ValueError):
            validate_user_id("12345")

    def test_password_rules(self):
        self.assertEqual(validate_password("Strong@123", "User_01"), "Strong@123")
        with self.assertRaises(ValueError):
            validate_password("weakpass", "user")

    def test_pickup_time_window(self):
        now = datetime.now() + timedelta(hours=1)
        dt = now.replace(hour=9, minute=0)
        self.assertIsNotNone(validate_pickup_datetime(dt.strftime("%Y-%m-%d"), "09:00"))


    def test_seed_has_multiple_collectors_and_admin_login_works(self):
        collectors = self.db.conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role='WasteCollector'"
        ).fetchone()["c"]
        self.assertGreaterEqual(collectors, 3)

        ok, status = self.db.verify_credentials("admin01", "Admin@1234")
        self.assertTrue(ok)
        self.assertEqual(status, "admin01")

    def test_end_to_end_points_awarded_only_completed(self):
        self.db.create_basic_user("resident01", "Resident@123")
        self.db.complete_profile(
            {
                "user_id": "resident01",
                "full_name": "Res One",
                "id_no": "ID12345",
                "telephone": "+60111111111",
                "email": "r1@example.com",
                "zone": "Zone A",
                "address": "Addr",
            }
        )
        dt = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        pid = self.db.create_pickup_with_recycling("resident01", dt, "Metal", 10, "")
        self.db.collector_update_pickup("collector01", pid, "COMPLETED", "done")
        row = self.db.conn.execute("SELECT points_awarded,current_status FROM pickup_request WHERE pickup_id=?", (pid,)).fetchone()
        self.assertEqual(row["current_status"], "COMPLETED")
        self.assertEqual(row["points_awarded"], 30)


if __name__ == "__main__":
    unittest.main()
