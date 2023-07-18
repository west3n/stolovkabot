from database.db_connection import connect


async def get_company_data(company_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM stolovka_company WHERE id = %s", (company_id,))
        return cur.fetchone()
    # Выдача: [0]:id, [1]:name, [2]:address, [3]:secret_key
    finally:
        cur.close()
        db.close()


async def get_company_data_by_key(secret_key):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM stolovka_company WHERE secret_key = %s", (secret_key,))
        return cur.fetchone()
    # Выдача: [0]:id, [1]:name, [2]:address, [3]:secret_key
    finally:
        cur.close()
        db.close()


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


async def get_all_key_list():
    db, cur = connect()
    try:
        cur.execute("SELECT secret_key FROM stolovka_company")
        return [key[0] for key in cur.fetchall()]
    finally:
        cur.close()
        db.close()
