import asyncio
import datetime
import re

from database.db_connection import connect


def extract_name_and_volume(dish_name):
    name_match = re.match(r'(.+?)\s+(\d+(\.\d+)?)\s*л\.', dish_name)
    if name_match:
        name = name_match.group(1)
        volume = float(name_match.group(2))
        return name, volume
    else:
        return None, None


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
            old_order_list = old_order.split("\n")
            old_order_names_list = [old_order_name.split(":")[0] for old_order_name in old_order_list]
            if order.split(":")[0] in old_order_names_list:
                for order_ in old_order_list:
                    if order.split(":")[0] == order_.split(":")[0]:
                        new_amount = int(order.split(":")[1].split(" ")[1]) + int(order_.split(":")[1].split(" ")[1])
                        new_order = f'{order_.split(":")[0]}: {new_amount} шт.'
                        old_order = old_order.replace(order_, new_order)
                    else:
                        pass
            else:
                old_order += f'\n{order}'
            if day == f"{day_of_week} ({nearest_date.strftime('%d.%m')})":
                cur.execute(f"UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                            f"WHERE customer_id = %s AND date = %s AND day = %s",
                            (old_order, price, tg_id, now, day))
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


async def update_basket_drink(tg_id, weekday, data, price):
    db, cur = connect()
    try:
        if weekday:
            cur.execute("SELECT \"order\" FROM dishes_basket WHERE customer_id = %s AND day = %s", (tg_id, weekday,))
        else:
            cur.execute("SELECT \"order\" FROM dishes_basket WHERE customer_id = %s", (tg_id,))
        old_order = cur.fetchone()
        old_order = old_order[0]
        old_order_list = old_order.split("\n")
        old_order_names_list = [old_order_name.split(":")[0] for old_order_name in old_order_list]
        if data.split(":")[0] in old_order_names_list:
            for order_ in old_order_list:
                if data.split(":")[0] == order_.split(":")[0]:
                    new_amount = int(data.split(":")[1].split(" ")[1]) + int(order_.split(":")[1].split(" ")[1])
                    new_order = f'{order_.split(":")[0]}: {new_amount} шт.'
                    old_order = old_order.replace(order_, new_order)
        else:
            old_order += f'\n{data}'
        if weekday:
            cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                        "WHERE customer_id = %s AND day = %s", (old_order, price, tg_id, weekday,))
            db.commit()
        else:
            cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                        "WHERE customer_id = %s", (old_order, price, tg_id,))
            db.commit()
    finally:
        db.close()
        cur.close()


async def update_basket_bakery(data, price, tg_id, weekday):
    db, cur = connect()
    try:
        cur.execute("SELECT \"order\" FROM dishes_basket WHERE customer_id = %s AND day = %s", (tg_id, weekday,))
        old_order = cur.fetchone()
        old_order = old_order[0]
        old_order_list = old_order.split("\n")
        old_order_names_list = [old_order_name.split(":")[0] for old_order_name in old_order_list]
        if data.split(":")[0] in old_order_names_list:
            for order_ in old_order_list:
                if data.split(":")[0] == order_.split(":")[0]:
                    new_amount = int(data.split(":")[1].split(" ")[1]) + int(order_.split(":")[1].split(" ")[1])
                    new_order = f'{order_.split(":")[0]}: {new_amount} шт.'
                    old_order = old_order.replace(order_, new_order)
        else:
            old_order += f'\n{data}'
        cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = price + %s "
                    "WHERE customer_id = %s AND day = %s", (old_order, price, tg_id, weekday,))
        db.commit()
    finally:
        db.close()
        cur.close()


async def get_basket(tg_id):
    db, cur = connect()
    try:
        cur.execute("SELECT day, \"order\", price FROM dishes_basket WHERE customer_id=%s", (tg_id,))
        result = cur.fetchall()
        return result
    finally:
        db.close()
        cur.close()


async def get_basket_sum(tg_id):
    db, cur = connect()
    try:
        cur.execute("SELECT SUM(price) FROM dishes_basket WHERE customer_id=%s", (tg_id,))
        result = cur.fetchone()
        return int(result[0]) if result[0] else 0
    finally:
        db.close()
        cur.close()


async def get_drinks():
    db, cur = connect()
    try:
        drink_1, drink_2 = 'Морс ягодный', 'Компот из сухофруктов'
        cur.execute("SELECT * FROM dishes_drink WHERE name = %s LIMIT 1", (drink_1,))
        result_1 = cur.fetchall()
        cur.execute("SELECT * FROM dishes_drink WHERE name = %s LIMIT 1", (drink_2,))
        result_2 = cur.fetchall()
        total_list = result_1 + result_2
        return total_list
    finally:
        db.close()
        cur.close()


async def get_drink_volumes():
    db, cur = connect()
    try:
        cur.execute("SELECT volume, price FROM dishes_drink WHERE name = %s ORDER BY price", ('Морс ягодный',))
        volumes = cur.fetchall()
        volume = [f'{volume}л. - {int(price)} ₽' for volume, price in volumes]
        return '\n'.join(volume)
    finally:
        db.close()
        cur.close()


async def get_drink_data(drink_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM dishes_drink WHERE id = %s", (drink_id,))
        return cur.fetchone()
    finally:
        db.close()
        cur.close()


async def get_drink_price(name, volume):
    db, cur = connect()
    try:
        cur.execute("SELECT price FROM dishes_drink WHERE name = %s AND volume = %s", (name, volume,))
        return cur.fetchone()
    finally:
        db.close()
        cur.close()


async def get_weekday_bake(weekday):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM dishes_bakery WHERE weekday = %s", (weekday,))
        return cur.fetchall()
    finally:
        db.close()
        cur.close()


async def get_bakery_data(drink_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM dishes_bakery WHERE id = %s", (drink_id,))
        return cur.fetchone()
    finally:
        db.close()
        cur.close()


async def get_full_basket(tg_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM dishes_basket WHERE customer_id=%s", (tg_id,))
        rows = cur.fetchall()
        items = {}
        data = []
        for row in rows:
            text = row[3]
            for line in text.split('\n'):
                parts = line.split(' : ')
                if len(parts) == 2:
                    item_description, quantity = parts[0], parts[1]
                    quantity_parts = quantity.split(' ')
                    if len(quantity_parts) == 2:
                        item_quantity = int(quantity_parts[0])
                        item_name = item_description
                        if item_name in items:
                            items[item_name] += item_quantity
                        else:
                            items[item_name] = item_quantity
            result_text = '\n'.join([f'{item} - {quantity} шт.' for item, quantity in items.items()])
            data.append([row[2], result_text, row[4]])
        return data
    finally:
        db.close()
        cur.close()


async def delete_basket(tg_id):
    db, cur = connect()
    try:
        cur.execute("DELETE FROM dishes_basket WHERE customer_id = %s", (tg_id,))
        db.commit()
    finally:
        db.close()
        cur.close()


async def get_basket_by_day(weekday, tg_id):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM dishes_basket WHERE customer_id=%s AND day = %s", (tg_id, weekday))
        return cur.fetchone()
    finally:
        db.close()
        cur.close()


async def delete_basket_by_day(weekday, tg_id):
    db, cur = connect()
    try:
        cur.execute("DELETE FROM dishes_basket WHERE customer_id=%s AND day = %s", (tg_id, weekday))
        db.commit()
    finally:
        db.close()
        cur.close()


async def search_name(dish):
    db, cur = connect()
    try:
        table_names = ['dishes_bakery', 'dishes_salad', 'dishes_soup', 'dishes_garnish', 'dishes_maindish']
        for table_name in table_names:
            cur.execute(f"SELECT name FROM {table_name} WHERE name ILIKE '%{dish}%'")
            result = cur.fetchone()
            if result:
                return result[0]
    finally:
        db.close()
        cur.close()


async def delete_dish_from_basket(dish_del, weekday, tg_id):
    db, cur = connect()
    try:
        basket = await get_basket_by_day(weekday, tg_id)
        existing_basket = basket[3]
        old_price = basket[4]
        existing_basket = existing_basket.replace(f"{dish_del}\n", "")
        if dish_del in existing_basket:
            existing_basket = existing_basket.replace(f"\n{dish_del}", "")
        if dish_del in existing_basket:
            existing_basket = existing_basket.replace(f"{dish_del}", "")
        if existing_basket:
            dish_del_name = dish_del.split(":")[0]
            dish_del_amount = int(dish_del.split(":")[1].split(" ")[1])
            table_names = ['dishes_bakery', 'dishes_salad', 'dishes_soup',
                           'dishes_garnish', 'dishes_maindish']
            price = 0
            for table_name in table_names:
                cur.execute(f"SELECT price FROM {table_name} WHERE name = %s", (dish_del_name[:-1],))
                result = cur.fetchone()
                if result:
                    price = result[0]
            if price == 0 or price is None:
                if dish_del_name[:-1].endswith('л.'):
                    name, volume = extract_name_and_volume(dish_del_name[:-1])
                    cur.execute(f'SELECT price FROM dishes_drink WHERE name = %s AND volume = %s', (name, volume,))
                    result = cur.fetchone()
                    price = result[0]
                else:
                    if dish_del_name.split('(')[1] == 'Полный обед)':
                        price = 280
                    else:
                        price = 260
            total_price = price * dish_del_amount
            new_price = old_price - total_price
            cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = %s WHERE day = %s AND customer_id = %s",
                        (existing_basket, new_price, weekday, tg_id,))
            db.commit()
        else:
            await delete_basket_by_day(weekday, tg_id)
    finally:
        db.close()
        cur.close()


async def change_dish_in_basket(tg_id, weekday, amount, dish):
    db, cur = connect()
    try:
        basket_data = await get_basket_by_day(weekday, tg_id)
        old_order = basket_data[3]
        old_price = basket_data[4]
        old_order_list = old_order.split("\n")
        for old_dish in old_order_list:
            if old_dish == dish:
                old_amount = old_dish.split(':')[1].split(" ")[1]
                new_dish = old_dish.replace(old_amount, amount)
                dish_name = old_dish.split(":")[0]
                table_names = ['dishes_bakery', 'dishes_salad', 'dishes_soup',
                               'dishes_garnish', 'dishes_maindish']
                price = 0
                for table_name in table_names:
                    cur.execute(f"SELECT price FROM {table_name} WHERE name = %s", (dish_name[:-1],))
                    result = cur.fetchone()
                    if result:
                        price = result[0]
                if price == 0 or price is None:
                    if dish_name[:-1].endswith('л.'):
                        name, volume = extract_name_and_volume(dish_name[:-1])
                        cur.execute(f'SELECT price FROM dishes_drink WHERE name = %s AND volume = %s', (name, volume,))
                        result = cur.fetchone()
                        price = result[0]
                    else:
                        if dish_name.split('(')[1] == 'Полный обед) ':
                            price = 280
                        else:
                            price = 260
                if int(old_amount) > int(amount):
                    difference = int(old_amount) - int(amount)
                    new_price = int(old_price) - (int(price) * difference)
                elif int(old_amount) == int(amount):
                    new_price = int(old_price)
                else:
                    difference = int(amount) - int(old_amount)
                    new_price = int(old_price) + (int(price) * difference)
                old_order = old_order.replace(old_dish, new_dish)
                cur.execute("UPDATE dishes_basket SET \"order\" = %s, price = %s WHERE day = %s AND customer_id = %s",
                            (old_order, new_price, weekday, tg_id,))
                db.commit()
    finally:
        db.close()
        cur.close()
