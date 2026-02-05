# Smart Waste Collection & Recycling System

Tkinter + SQLite desktop prototype for university demo.

## Run
```bash
python main.py
```

## Default seeded accounts
| Role | User ID | Password |
|---|---|---|
| MunicipalAdmin | `Admin001` | `Admin123A` |
| WasteCollector | `Collect1` | `Collect123A` |

## Feature checklist (prototype)
- [x] User registration + authentication (validated User ID/password + hashed password)
- [x] Resident onboarding form with scrollable frame and labeled fields
- [x] Back-button navigation between screens
- [x] Resident pickup scheduling and pickup history
- [x] Collector pickup worklist + status workflow (IN_PROGRESS/COMPLETED/FAILED with fail reason)
- [x] Offline route-order simulation (deterministic heuristic)
- [x] Recycling log submission (type, weight, optional image upload)
- [x] Reward points and recycling history
- [x] Notification module (admin send + automatic status updates + pickup reminders)
- [x] Dashboard metrics (simulated waste volume & recycling rate)
- [x] Admin settings: zone CRUD, user CRUD, collector-zone assignment, monitoring stats
- [x] Logging to `logs/app.log`

## Notes
- Notifications are in-app only (stored in SQLite).
- Upload images are copied to `uploads/`.
- Database file is created at `db/prototype.db`.
