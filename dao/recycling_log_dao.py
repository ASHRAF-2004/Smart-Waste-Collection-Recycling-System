class RecyclingLogDAO:
    def __init__(self, db):
        self.db = db

    def create_log(self, conn, resident_id, category, weight_kg, logged_at, waste_image=None):
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO recycling_log(resident_id,category,weight_kg,logged_at,waste_image) VALUES (?,?,?,?,?)",
            (resident_id, category, weight_kg, logged_at, waste_image),
        )

    def list_by_resident(self, resident_id):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM recycling_log WHERE resident_id=? ORDER BY log_id DESC", (resident_id,))
            return cur.fetchall()
