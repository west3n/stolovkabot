import datetime

from database import db_customer, db_basket
from database.db_connection import connect


async def add_new_order(tg_id):
    db, cur = connect()
    try:
        user_data = await db_customer.get_customer(tg_id)
        order_data = await db_basket.get_full_basket(tg_id)
        now = datetime.datetime.now().date()
        for data in order_data:
            print(data)
            order_text = f'{data[0]} - {data[1]}'
            cur.execute('INSERT INTO orders_order (address, approve, company_id, customer_id, '
                        'amount, order_date, order_text) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (user_data[4], False, user_data[3], tg_id, data[2], now, order_text,))
            db.commit()
    finally:
        db.close()
        cur.close()
