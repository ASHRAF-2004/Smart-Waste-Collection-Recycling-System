"""Desktop prototype entrypoint for Smart Waste Collection and Recycling System."""
from controllers.app_controller import SmartWasteApp


if __name__ == "__main__":
    app = SmartWasteApp()
    app.mainloop()
