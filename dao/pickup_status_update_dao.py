class PickupStatusUpdateDAO:
    def __init__(self, db):
        self.db = db

    def create_update(self, conn, pickup_id, collector_id, new_status, timestamp, comment=None, evidence_image=None):
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO pickup_status_update
            (pickup_id,updated_by_collector_id,new_status,timestamp,comment,evidence_image)
            VALUES (?,?,?,?,?,?)""",
            (pickup_id, collector_id, new_status, timestamp, comment, evidence_image),
        )

    def list_by_pickup(self, pickup_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT s.*, u.name AS collector_name FROM pickup_status_update s JOIN users u ON s.updated_by_collector_id=u.user_id WHERE pickup_id=? ORDER BY status_update_id DESC",
                (pickup_id,),
            )
            return cur.fetchall()
