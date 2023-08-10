from database.db_connection import connect

lunches = {
    'diet': 'Диетический',
    'vegan': 'Веганский',
    'lunch1': 'Обед 1',
    'lunch2': 'Обед 2',
    'lunch3': 'Обед 3',
    'lunch4': 'Обед 4',
    'lunch5': 'Обед 5'
}


async def get_lunch_name(lunch_id):
    db, cur = connect()
    try:
        cur.execute("SELECT lunch FROM dishes_complex WHERE id = %s", (lunch_id,))
        value = lunches.get(cur.fetchone()[0])
        return value
    finally:
        cur.close()
        db.close()


async def get_all_lunches_by_weekday(weekday):
    db, cur = connect()
    try:
        cur.execute("SELECT * FROM dishes_complex WHERE weekday = %s", (weekday,))
        results = cur.fetchall()
        list_results = []
        for result in results:
            cur.execute("SELECT name, image_id, calories, protein, fat, carbohydrates, ingredients "
                        "FROM dishes_salad WHERE id = %s", (result[5],))
            salad = cur.fetchone()
            cur.execute("SELECT name, image_id, calories, protein, fat, carbohydrates, ingredients "
                        "FROM dishes_soup WHERE id = %s", (result[6],))
            soup = cur.fetchone()
            cur.execute("SELECT name, image_id, calories, protein, fat, carbohydrates, ingredients "
                        "FROM dishes_maindish WHERE id = %s", (result[4],))
            main_dish = cur.fetchone()
            cur.execute("SELECT name, image_id, calories, protein, fat, carbohydrates, ingredients "
                        "FROM dishes_garnish WHERE id = %s", (result[3],))
            garnish = cur.fetchone()
            total_calories = round(salad[2] + soup[2] + main_dish[2] + (garnish[2] if garnish else 0), 2)
            total_protein = round(salad[3] + soup[3] + main_dish[3] + (garnish[3] if garnish else 0), 2)
            total_fat = round(salad[4] + soup[4] + main_dish[4] + (garnish[4] if garnish else 0), 2)
            total_carbohydrates = round(salad[5] + soup[5] + main_dish[5] + (garnish[5] if garnish else 0), 2)
            list_results += [[salad[0], salad[1], salad[6], soup[0], soup[1], soup[6], main_dish[0], main_dish[1],
                             main_dish[6], garnish[0] if garnish else None, garnish[1] if garnish else None,
                              garnish[6] if garnish else None, total_calories, total_protein, total_fat,
                              total_carbohydrates, result[2], result[0]]]
        return list_results
    finally:
        cur.close()
        db.close()


async def get_lunch_price(lunch_id):
    db, cur = connect()
    try:
        cur.execute("SELECT full_price, price_wo_salad, price_wo_soup FROM dishes_complex WHERE id=%s", (lunch_id,))
        return cur.fetchone()
    finally:
        cur.close()
        db.close()
