from database.db_connection import connect


async def get_customer(tg_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM stolovka_customer WHERE tg_id = %s", (tg_id,))
        return cur.fetchone()
        # Выдача: [0]:tg_id, [1]:phone_number, [2]:name, [3]:company_id, [4]:address
    finally:
        cur.close()
        db.close()


async def insert_individual_customer(data, tg_id):
    db, cur = connect()
    try:
        cur.execute("INSERT INTO stolovka_customer (tg_id, phone_number, name, company_id, address) "
                    "VALUES (%s, %s, %s, %s, %s)", (tg_id, data.get('phone'), data.get('name'), data.get('company_id'),
                                                    data.get('address'),))
        db.commit()
    finally:
        cur.close()
        db.close()


async def update_phone(tg_id, phone):
    db, cur = connect()
    try:
        cur.execute("UPDATE stolovka_customer SET phone_number = %s WHERE tg_id = %s", (phone, tg_id,))
        db.commit()
    finally:
        cur.close()
        db.close()


async def update_address(tg_id, address):
    db, cur = connect()
    try:
        cur.execute("UPDATE stolovka_customer SET address = %s WHERE tg_id = %s", (address, tg_id,))
        db.commit()
    finally:
        cur.close()
        db.close()


async def get_orders(tg_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM orders_order WHERE customer_id = %s", (tg_id,))
        return cur.fetchall()
    finally:
        cur.close()
        db.close()
