class NotificationDAO:
    def __init__(self, db):
        self.db = db

    def create_notification(self, user_id, title, message, created_at):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notification(user_id,title,message,created_at,read_at) VALUES (?,?,?,?,NULL)",
                (user_id, title, message, created_at),
            )
            conn.commit()
            return cur.lastrowid

    def list_for_user(self, user_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM notification WHERE user_id=? ORDER BY notification_id DESC", (user_id,))
            return cur.fetchall()

    def mark_read(self, user_id, notification_id, read_at):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE notification SET read_at=? WHERE notification_id=? AND user_id=?",
                (read_at, notification_id, user_id),
            )
            conn.commit()
