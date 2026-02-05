class PickupRequestDAO:
    def __init__(self, db):
        self.db = db

    def create_request(self, resident_id, zone_id, requested_datetime, status="PENDING"):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO pickup_request(resident_id,zone_id,requested_datetime,status) VALUES (?,?,?,?)",
                (resident_id, zone_id, requested_datetime, status),
            )
            conn.commit()
            return cur.lastrowid

    def list_by_resident(self, resident_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pickup_request WHERE resident_id=? ORDER BY pickup_id DESC", (resident_id,))
            return cur.fetchall()

    def list_by_zone(self, zone_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT p.*, u.name AS resident_name FROM pickup_request p JOIN users u ON p.resident_id=u.user_id WHERE p.zone_id=? ORDER BY CASE p.status WHEN 'PENDING' THEN 0 ELSE 1 END, p.pickup_id DESC",
                (zone_id,),
            )
            return cur.fetchall()

    def get_by_id(self, pickup_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pickup_request WHERE pickup_id=?", (pickup_id,))
            return cur.fetchone()

    def update_status(self, conn, pickup_id, new_status):
        cur = conn.cursor()
        cur.execute("UPDATE pickup_request SET status=? WHERE pickup_id=?", (new_status, pickup_id))
