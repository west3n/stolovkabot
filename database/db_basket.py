import datetime
from database.db_connection import connect


async def insert_basket(tg_id, order, price):
    db, cur = connect()
    try:
        now = datetime.datetime.now().date()
        cur.execute("INSERT INTO dishes_basket (customer_id, date, \"order\", price) VALUES (%s, %s, %s, %s)",
                    (tg_id, now, order, price))
        db.commit()
    finally:
        db.close()
        cur.close()


async def update_basket(tg_id, order, price):
    db, cur = connect()
    try:
        now = datetime.datetime.now().date()
        cur.execute("SELECT \"order\" FROM dishes_basket WHERE date=%s AND customer_id=%s", (now, tg_id,))
        existing_order = cur.fetchone()
        new_order = ''
        if existing_order:
            existing_order = existing_order[0]
            new_order = f"{existing_order}\n{order}"
        cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                    "WHERE customer_id=%s", (new_order, price, tg_id,))
        db.commit()
    finally:
        db.close()
        cur.close()
