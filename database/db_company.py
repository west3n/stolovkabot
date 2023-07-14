from database.db_connection import connect


async def get_all_companies_names():
    db, cur = connect()
    try:
        cur.execute("SELECT name FROM stolovka_company")
        return [name[0] for name in cur.fetchall()]
    finally:
        cur.close()
        db.close()


async def add_new_company(data, secret_key):
    db, cur = connect()
    try:
        cur.execute("INSERT INTO stolovka_company (name, address, secret_key) VALUES (%s, %s, %s) RETURNING id",
                    (data.get('name'), data.get('address'), secret_key,))
        db.commit()
        return cur.fetchone()[0]
    finally:
        cur.close()
        db.close()
