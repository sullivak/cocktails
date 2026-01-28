import sqlite3
from flask import Flask, render_template, request

from config import DB_PATH

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_ingredients():
    conn = get_db_connection()
    ingredients = conn.execute(
        'SELECT link_name, synonyms_csv FROM ingredients ORDER BY link_name'
    ).fetchall()
    conn.close()
    return ingredients


def get_cocktails_by_ingredient(ingredient_link_name):
    conn = get_db_connection()

    # Get ingredient ID
    ingredient = conn.execute(
        'SELECT ingredient_id FROM ingredients WHERE link_name = ?',
        (ingredient_link_name,)
    ).fetchone()

    if not ingredient:
        conn.close()
        return []

    # Get matching cocktails with their details
    cocktails = conn.execute('''
        SELECT DISTINCT c.link_name, c.drinkware, c.prep, c.garnish, c.served
        FROM cocktails c
        JOIN cocktail_contents cc ON cc.cocktail_id = c.cocktail_id
        WHERE cc.ingredient_id = ?
        ORDER BY c.link_name
    ''', (ingredient['ingredient_id'],)).fetchall()

    conn.close()
    return cocktails


def get_cocktail_ingredients(cocktail_link_name):
    conn = get_db_connection()

    ingredients = conn.execute('''
        SELECT i.link_name, i.synonyms_csv, cc.amt_value, cc.amt_unit
        FROM ingredients i
        JOIN cocktail_contents cc ON cc.ingredient_id = i.ingredient_id
        JOIN cocktails c ON c.cocktail_id = cc.cocktail_id
        WHERE c.link_name = ?
        ORDER BY i.link_name
    ''', (cocktail_link_name,)).fetchall()

    conn.close()
    return ingredients


def format_cocktail_name(link_name):
    """Convert 'Cocktail_Name+Variation' to 'Cocktail Name (Variation)'"""
    if '+' in link_name:
        base, variation = link_name.split('+', 1)
        return f"{base.replace('_', ' ')} ({variation})"
    return link_name.replace('_', ' ')


def format_ingredient_name(link_name):
    """Convert 'ingredient_name' to 'Ingredient Name'"""
    return link_name.replace('_', ' ').title()


# Make formatters available in templates
app.jinja_env.globals.update(
    format_cocktail_name=format_cocktail_name,
    format_ingredient_name=format_ingredient_name
)


@app.route('/')
def index():
    ingredients = get_all_ingredients()
    selected = request.args.get('ingredient', '')
    cocktails = []

    if selected:
        cocktails = get_cocktails_by_ingredient(selected)

    return render_template('index.html',
                           ingredients=ingredients,
                           selected=selected,
                           cocktails=cocktails)


@app.route('/cocktail/<path:name>')
def cocktail_detail(name):
    conn = get_db_connection()

    cocktail = conn.execute(
        'SELECT * FROM cocktails WHERE link_name = ?',
        (name,)
    ).fetchone()

    if not cocktail:
        conn.close()
        return "Cocktail not found", 404

    ingredients = get_cocktail_ingredients(name)
    conn.close()

    return render_template('cocktail.html',
                           cocktail=cocktail,
                           ingredients=ingredients)


if __name__ == '__main__':
    app.run(debug=True)
