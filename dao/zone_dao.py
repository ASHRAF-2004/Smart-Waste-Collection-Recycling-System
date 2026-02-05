class ZoneDAO:
    def __init__(self, db):
        self.db = db

    def list_zones(self):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM zone ORDER BY zone_name")
            return cur.fetchall()

    def create_zone(self, zone_name):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO zone(zone_name) VALUES (?)", (zone_name,))
            conn.commit()
            return cur.lastrowid

    def update_zone(self, zone_id, zone_name):
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE zone SET zone_name=? WHERE zone_id=?", (zone_name, zone_id))
            conn.commit()
