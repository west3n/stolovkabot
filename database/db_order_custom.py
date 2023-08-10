import asyncio

from database.db_connection import connect


async def get_dish_by_day(dish_type, day):
    db, cur = connect()
    try:
        cur.execute(f'SELECT * from dishes_{dish_type} WHERE weekdays LIKE %s', (f'%{day}%',))
        return cur.fetchall()
    finally:
        db.close()
        cur.close()


async def get_dish_info(dish_type, dish_id):
    db, cur = connect()
    try:
        cur.execute(f'SELECT * from dishes_{dish_type} WHERE id = %s', (dish_id,))
        return cur.fetchone()
    finally:
        db.close()
        cur.close()
