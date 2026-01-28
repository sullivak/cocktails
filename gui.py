import sqlite3
import PySimpleGUI as sg

from config import DB_PATH


def launch_gui():
    """Run the PySimpleGUI ingredient browser (desktop GUI)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    select_id_string = 'SELECT link_name, synonyms_csv FROM ingredients'
    c.execute(select_id_string)
    all_ingredients = c.fetchall()
    display_ingredients = [tup[0] for tup in all_ingredients]

    sg.theme('DarkAmber')
    layout = [
        [sg.Text('Select an ingredient')],
        [sg.Button('Ok'), sg.Button('Cancel')],
        [sg.Combo(display_ingredients)]
    ]

    window = sg.Window('Booze Browser', layout)
    while True:
        event, values = window.read()
        print("event", event)
        print("values", values)
        if event in (None, 'Cancel'):
            break
        print('You entered ', values[0])
        chosen_ingredient = values[0]
        get_ing_id_str = 'SELECT ingredient_id FROM ingredients WHERE link_name = "{0}"'.format(chosen_ingredient)
        c.execute(get_ing_id_str)
        ingredient_id = c.fetchone()[0]
        get_matching_cocktails_str = '''
            SELECT cocktails.link_name
            FROM cocktails, cocktail_contents
            WHERE cocktail_contents.cocktail_id = cocktails.cocktail_id
            AND cocktail_contents.ingredient_id = {0}
        '''.format(ingredient_id)
        c.execute(get_matching_cocktails_str)
        all_cocktails = c.fetchall()
        all_cocktails = [tup[0] for tup in all_cocktails]

        print(all_cocktails)

        choose_cocktail_layout = [[sg.Combo(all_cocktails)]]
        window2 = sg.Window("window 2", choose_cocktail_layout)
        event, values = window2.read()

    window.close()
    conn.close()


if __name__ == "__main__":
    launch_gui()
