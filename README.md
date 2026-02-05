# Smart Waste Collection & Recycling System

## Intro
This project is a desktop prototype for a **Smart Waste Collection and Recycling System** built with Python and Tkinter.

It currently includes:
- Login and registration flows.
- A multi-step resident onboarding process.
- Dashboard screens for different user roles.
- Local SQLite storage for user and profile data.

The app starts from `main.py`, launches a Tkinter GUI, and initializes a local SQLite database at `db/prototype.db`.

## Requirements
- Python 3.10+ (3.9+ may also work)
- Tkinter (usually included with standard Python installations)
- SQLite3 (included in Python standard library)

No third-party Python packages are required for the current prototype.

## How to run
1. Open a terminal in the project root.
2. Run the application:

```bash
python main.py
```

If your system maps Python 3 to `python3`, use:

```bash
python3 main.py
```

On first run, the app will create the local database file automatically under `db/prototype.db`.
