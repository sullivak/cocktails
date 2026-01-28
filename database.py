import os
import sqlite3

from config import DATA_DIR, DB_PATH


def init_database():
    """Create the SQLite database schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("CREATE TABLE ingredients (ingredient_id INTEGER PRIMARY KEY, link_name TEXT, synonyms_csv TEXT)")
    c.execute("CREATE TABLE cocktails (cocktail_id INTEGER PRIMARY KEY, link_name TEXT, is_IBA INT, drinkware TEXT, prep TEXT, garnish TEXT, footnote TEXT, served TEXT)")
    c.execute("CREATE TABLE cocktail_contents (cocktail_id INT, ingredient_id INT, amt_value REAL, amt_unit TEXT)")

    conn.close()


def store_all_data(all_cocktails_data, all_ingredients):
    """Populate the SQLite database with parsed cocktail and ingredient data."""
    if not os.path.exists(DB_PATH):
        init_database()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    insert_string_template = 'INSERT INTO ingredients VALUES (NULL, "{0}", "{1}")'
    for ingredient_key, ingredient_value in all_ingredients.items():
        insert_string = insert_string_template.format(ingredient_key, ",".join(ingredient_value))
        try:
            c.execute(insert_string)
        except sqlite3.OperationalError as e:
            print(e)
    conn.commit()

    insert_string_template = 'INSERT INTO cocktails VALUES (NULL, "{0}", {1}'
    for cocktail_key, cocktail_value in all_cocktails_data.items():
        if 'iba' in cocktail_value and cocktail_value['iba'].lower() == 'yes':
            iba_int = 1
        else:
            iba_int = 0
        insert_string = insert_string_template.format(cocktail_key, iba_int)
        next_text_template = ', "{0}"'
        if 'drinkware' in cocktail_value:
            insert_string += next_text_template.format(cocktail_value['drinkware'])
        else:
            insert_string += ", NULL"
        if 'prep' in cocktail_value:
            insert_string += next_text_template.format(cocktail_value['prep'])
        else:
            insert_string += ", NULL"
        if 'garnish' in cocktail_value:
            insert_string += next_text_template.format(cocktail_value['garnish'])
        else:
            insert_string += ", NULL"
        if 'footnote' in cocktail_value:
            insert_string += next_text_template.format(cocktail_value['footnote'])
        else:
            insert_string += ", NULL"
        if 'served' in cocktail_value:
            insert_string += next_text_template.format(cocktail_value['served'])
        else:
            insert_string += ", NULL"

        insert_string += ')'
        try:
            c.execute(insert_string)
        except sqlite3.OperationalError as e:
            print("sqlite3.OperationalError", e, "insert_string:", insert_string)
    conn.commit()

    for cocktail_key, cocktail_value in all_cocktails_data.items():
        select_id_string = 'SELECT cocktail_id FROM cocktails WHERE link_name = "{0}"'.format(cocktail_key)
        c.execute(select_id_string)
        try:
            cocktail_id = c.fetchone()[0]
        except Exception as e:
            print(e)
            raise e
        if cocktail_id is None:
            print("Could not find", cocktail_key)
            continue

        for ingredient in cocktail_value['ingredients_clean']:
            select_id_string = 'SELECT ingredient_id FROM ingredients WHERE link_name = "{0}"'.format(ingredient['ing'][0])
            c.execute(select_id_string)
            try:
                ingredient_id = c.fetchone()[0]
            except Exception as e:
                print(e)
                raise e
            amt_value, amt_unit = ingredient['amt']
            insert_string = 'INSERT INTO cocktail_contents VALUES ({0}, {1}, {2}, "{3}")'.format(
                cocktail_id, ingredient_id, amt_value, amt_unit
            )
            try:
                c.execute(insert_string)
            except sqlite3.OperationalError as e:
                print("sqlite3.OperationalError", e, "insert_string:", insert_string)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    from parser import parse_all_raw_text
    all_cocktails_data, all_ingredients = parse_all_raw_text()
    store_all_data(all_cocktails_data, all_ingredients)
    print("Database populated successfully")
