"""Notification send/read service."""
import sqlite3

from utils.errors import DatabaseError
from utils.time_utils import now_iso
from utils.validators import require_text


class NotificationService:
    def __init__(self, notification_dao, auth_service):
        self.notification_dao = notification_dao
        self.auth_service = auth_service

    def send_to_user(self, admin_user, user_id, title, message):
        self.auth_service.ensure_role(admin_user, ["MunicipalAdmin"])
        title = require_text(title, "Title")
        message = require_text(message, "Message")
        try:
            return self.notification_dao.create_notification(int(user_id), title, message, now_iso())
        except sqlite3.Error as exc:
            print(f"[DB] send notification failure: {exc}")
            raise DatabaseError("Could not send notification.")

    def list_my_notifications(self, user):
        return self.notification_dao.list_for_user(user["user_id"])

    def mark_read(self, user, notification_id):
        try:
            self.notification_dao.mark_read(user["user_id"], int(notification_id), now_iso())
        except sqlite3.Error as exc:
            print(f"[DB] mark read failure: {exc}")
            raise DatabaseError("Could not mark notification as read.")
