import asyncio
import datetime
import re
from collections import defaultdict

from database.db_connection import connect


def get_nearest_weekday(target_weekday):
    days_of_week = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
    current_day = datetime.datetime.now().weekday()
    target_day = days_of_week[target_weekday]
    days_until_target = (target_day - current_day) % 7
    nearest_date = datetime.datetime.now() + datetime.timedelta(days=days_until_target)
    return nearest_date


async def insert_basket(weekday, tg_id, order, price):
    days_of_week_ru_full = {
        'mon': 'Понедельник',
        'tue': 'Вторник',
        'wed': 'Среда',
        'thu': 'Четверг',
        'fri': 'Пятница',
        'sat': 'Суббота',
        'sun': 'Воскресенье'
    }
    db, cur = connect()
    now = datetime.datetime.now().date()
    nearest_date = get_nearest_weekday(weekday)
    day_of_week = days_of_week_ru_full[weekday]
    try:
        cur.execute("SELECT day, \"order\" FROM dishes_basket WHERE date = %s AND customer_id = %s", (now, tg_id,))
        row = cur.fetchone()
        if row:
            day, old_order = row
            new_order = old_order + f"\n{order}"
            if day == f"{day_of_week} ({nearest_date.strftime('%d.%m')})":
                cur.execute(f"UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                            f"WHERE customer_id = %s AND date = %s AND day = %s",
                            (new_order, price, tg_id, now, day))
                db.commit()
            else:
                cur.execute("INSERT INTO dishes_basket (customer_id, date, day, \"order\", price) VALUES "
                            "(%s, %s, %s, %s, %s)", (tg_id, now, f"{day_of_week} ({nearest_date.strftime('%d.%m')})",
                                                     order, price))
                db.commit()
        else:
            cur.execute("INSERT INTO dishes_basket (customer_id, date, day, \"order\", price) VALUES "
                        "(%s, %s, %s, %s, %s)", (tg_id, now, f"{day_of_week} ({nearest_date.strftime('%d.%m')})",
                                                 order, price))
            db.commit()
    finally:
        db.close()
        cur.close()


async def update_basket(weekday, tg_id, order, price):
    days_of_week_ru_full = {
        'mon': 'Понедельник',
        'tue': 'Вторник',
        'wed': 'Среда',
        'thu': 'Четверг',
        'fri': 'Пятница',
        'sat': 'Суббота',
        'sun': 'Воскресенье'
    }
    db, cur = connect()
    try:
        now = datetime.datetime.now().date()
        if weekday:
            nearest_date = get_nearest_weekday(weekday)
            day_of_week = days_of_week_ru_full[weekday]
            order = f"{day_of_week} ({nearest_date.strftime('%d.%m')}):\n{order}"
        cur.execute("SELECT \"order\" FROM dishes_basket WHERE date=%s AND customer_id=%s", (now, tg_id,))
        existing_order = cur.fetchone()
        new_order = f"{existing_order[0]}\n{order}" if existing_order else ''
        cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                    "WHERE customer_id=%s", (new_order, price, tg_id,))
        db.commit()
    finally:
        db.close()
        cur.close()
