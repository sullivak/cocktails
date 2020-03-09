
import os
import urllib.request
import sqlite3
import re
import glob
import PySimpleGUI as sg
import xml.etree.ElementTree as ET


output_base_dir = "/home/sullivak/Data/Cocktails"


def get_all_raw_text():
    base_url = "https://en.wikipedia.org/wiki/Special:Export/List_of_IBA_official_cocktails"
    # TODO: "https://en.wikipedia.org/wiki/List_of_cocktails"
    output_dir = os.path.join(output_base_dir, "cocktail_raw_txts")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    cocktail_url_template = "https://en.wikipedia.org/wiki/Special:Export/{0}"
    weird_prefix = "{http://www.mediawiki.org/xml/export-0.10/}"
    link_regex = "\[\[(.* ?)\]\]"
    link_regex = re.compile(link_regex)
    is_cocktail_string = "Infoboxcocktail|iba=yes"

    with urllib.request.urlopen(base_url) as response:
        list_xml_b = response.read()

    root = ET.fromstring(list_xml_b)
    page_root = root.find(weird_prefix + "page")
    revision_root = page_root.find(weird_prefix + 'revision')
    text_root = revision_root.find(weird_prefix + 'text')
    raw_text = text_root.text

    link_matches = re.finditer(link_regex, raw_text)
    for m in link_matches:
        # print("0", m.group(0), "1", m.group(1)) # "0", m.group(1), "2", m.group(2)
        link_name = m.group(1)
        link_name = link_name.split("|")[0]
        link_name = link_name.replace(" ", "_")
        cocktail_url = cocktail_url_template.format(link_name)
        try:
            with urllib.request.urlopen(cocktail_url) as response:
                page_xml_b = response.read()
            root = ET.fromstring(page_xml_b)
            page_root = root.find(weird_prefix + "page")
            revision_root = page_root.find(weird_prefix + 'revision')
            text_root = revision_root.find(weird_prefix + 'text')
            raw_text = text_root.text
            no_space_text = "".join(raw_text.split())
            # if "Aviation" in link_name:
            if is_cocktail_string in no_space_text:
                if "#REDIRECT" in no_space_text:
                    print(link_name)
                out_txt_path = os.path.join(output_dir, link_name + ".txt")
                try:
                    with open(out_txt_path, 'w') as f:
                        raw_text_lines = raw_text.split("\n")
                        raw_text_lines = [a + "\n" for a in raw_text_lines]
                        f.writelines(raw_text_lines)
                except Exception as e:
                    print("couldn't write out", out_txt_path, str(e))
        except Exception as e:
            print("issue with", cocktail_url, str(e))
            # "issue with https://en.wikipedia.org/wiki/Special:Export/Piña_Colada 'ascii' codec can't encode character '\xf1' in position 27: ordinal not in range(128)"
            # just got Piña_Colada manually (using curl to keep newlines) :/, next time use requests?

def infobox_line_to_kv_pair(line):
    if "=" in line:
        parts = line.split("=")
        key = parts[0]
        value = "=".join(parts[1::])
        key = key.replace("|", "")
        key = "".join(key.split())
        value = value.rstrip()
        value = value.lstrip()
        damn_sazerac_ref = value.find("<ref")
        if damn_sazerac_ref != -1:
            value = value[0:damn_sazerac_ref]
    else:
        key = "null"
        value = "null"
    return key, value

def write_dirty_cocktails(all_cocktails_data):
    all_ingredients = set()
    for cocktail_name, cocktail_data in all_cocktails_data.items():
        print(cocktail_name)
        cocktail_ingredients = []
        for raw_ingredient in cocktail_data['ingredients_raw']:
            if raw_ingredient[0] == "|":
                raw_ingredient = raw_ingredient[1::]
            raw_ingredient = raw_ingredient.replace("ingredients =", "")
            raw_ingredient = raw_ingredient.replace("*", "")
            raw_ingredient = raw_ingredient.lstrip()

            amt_regex = "([0-9]+(\.|\s)?[0-9]*\s?(cl|ml|dash|dashes|teaspoons|drops|splash)?)"
            match = re.search(amt_regex, raw_ingredient)
            if match is None:
                cocktail_ingredients.append({'amt': (raw_ingredient, "???"), 'ing': (raw_ingredient, "???")})
                all_ingredients.add((raw_ingredient, "???"))
            else:
                raw_amt = match.group(0)
                amt_quant_regex = "([0-9]+(\.|\s)?[0-9]*)"
                match = re.search(amt_quant_regex, raw_amt)
                if match is None:
                    amt_quant = raw_amt
                    amt_measure = "???"
                else:
                    amt_quant = match.group(0)
                    amt_measure = raw_amt.replace(amt_quant, "")
                    amt_measure = amt_measure.replace(" ", "")
                just_ingredient = raw_ingredient.replace(amt_quant, "")
                just_ingredient = just_ingredient.replace(amt_measure, "")
                linked_ing_regex = "\[\[(.+)\]\]"
                match = re.search(linked_ing_regex, just_ingredient)
                if match is None:
                    print("WAH!!!", cocktail_name)
                    ing_name = just_ingredient.strip()
                    ing_link = "???"
                else:
                    linked_ing = match.group(1)
                    if "|" in linked_ing:
                        ing_link, ing_name = linked_ing.split("|")
                    else:
                        ing_link = ing_name = linked_ing

                cocktail_ingredients.append({'amt': (amt_quant.rstrip(), amt_measure), 'ing': (ing_link, ing_name)})
                all_ingredients.add((ing_link, ing_name))
        all_cocktails_data[cocktail_name]['ingredients'] =  cocktail_ingredients

    out_lines = []
    for cocktail_name, cocktail_data in all_cocktails_data.items():
        out_lines.append("###\n")
        out_lines.append(cocktail_name + "\n")
        for ingredient in cocktail_data['ingredients']:
            out_line = "amt: {0},{1}, ing: {2},{3}\n".format(ingredient['amt'][0], ingredient['amt'][1], ingredient['ing'][0], ingredient['ing'][1])
            out_lines.append(out_line)

    with open("/home/sullivak/Data/Cocktails/cocktail_ings_to_clean.txt", 'w') as fp:
        fp.writelines(out_lines)


def parse_all_raw_text():
    in_dir = os.path.join(output_base_dir, "cocktail_raw_txts")
    # infobox_regex = "\{\{Infobox cocktail(.* ?)\}\}"
    infobox_start = "{{Infobox cocktail"
    # infobox_regex = re.compile(infobox_start)
    # "https://en.wikipedia.org/wiki/Sidecar_(cocktail)#/media/File:Sidecar-cocktail.jpg"
    all_raw_paths = glob.glob(os.path.join(in_dir, "*.txt"))
    # all_raw_paths = ['/home/sullivak/Data/Cocktails/cocktail_raw_txts/Fizz_(cocktail)#Gin_fizz.txt']
    # all_raw_paths = ['/home/sullivak/Data/Cocktails/cocktail_raw_txts/Pisco_sour.txt']

    all_cocktails_data = {}
    for path in all_raw_paths:
        cocktail_name = os.path.basename(path)
        cocktail_name = cocktail_name.split(".")[0]

        with open(path, 'r') as f:
            infobox_open = False
            variation_cnt = 0
            all_lines = f.readlines()
            for line in all_lines:
                if not infobox_open and infobox_start in line:
                    infobox_open = True
                    ingredients_open = False
                    a_cocktail_data = {}
                    ingredients_lines = []
                elif infobox_open:
                    if "}}" in line:
                        infobox_open = False
                        if len(ingredients_lines) > 0:
                            variation_cnt += 1
                            a_cocktail_data['ingredients_raw'] = ingredients_lines
                            all_cocktails_data[cocktail_name + "+" + a_cocktail_data["name"]] = a_cocktail_data
                    else:
                        if "| ingredients" in line or "|ingredients" in line:
                            ingredients_open = True
                            ingredients_lines.append(line.rstrip())
                        elif "| prep" in line or "|prep" in line:
                            ingredients_open = False
                            k, v = infobox_line_to_kv_pair(line)
                            a_cocktail_data[k] = v
                        elif ingredients_open:
                            ingredients_lines.append(line.rstrip())
                        else:
                            k, v = infobox_line_to_kv_pair(line)
                            a_cocktail_data[k] = v


    # write_dirty_cocktails(all_cocktails_data)
    # manually cleaned up some of the tricker stuff, parse this cleaned version
    with open("/home/sullivak/Data/Cocktails/cocktail_ings_cleaned.txt", 'r') as fp:
        all_lines = fp.readlines()

    start_new = False
    clean_ingredients = None
    all_ingredients = dict()
    most_ingredients = 0
    for line in all_lines:
        line = line.rstrip()

        if start_new:
            cocktail_name = line
            start_new = False
            clean_ingredients = []
            continue
        if line == "###":
            if clean_ingredients is not None:
                all_cocktails_data[cocktail_name]['ingredients_clean'] = clean_ingredients
                if len(clean_ingredients) > most_ingredients:
                    most_ingredients = len(clean_ingredients)
            start_new = True
            continue

        amt_string, ing_string = line.split(", ing: ")
        amt_string = amt_string.replace("amt: ", "")
        amt_quant, amt_measure = amt_string.split(",")
        ing_link, ing_name = ing_string.split(",")
        ing_link = ing_link.lower()
        ing_name = ing_name.lower()
        clean_ingredients.append({'amt': (float(amt_quant.strip()), amt_measure.strip()), 'ing': (ing_link, ing_name)})
        if ing_link in all_ingredients:
            all_ingredients[ing_link].add(ing_name)
        else:
            all_ingredients[ing_link] = {ing_name}


    return all_cocktails_data, all_ingredients


def init_database():
    conn = sqlite3.connect(os.path.join(output_base_dir, "cocktails.db"))
    c = conn.cursor()

    c.execute("CREATE TABLE ingredients (ingredient_id INTEGER PRIMARY KEY, link_name TEXT, synonyms_csv TEXT)")
    c.execute("CREATE TABLE cocktails (cocktail_id INTEGER PRIMARY KEY, link_name TEXT, is_IBA INT, drinkware TEXT, prep TEXT, garnish TEXT, footnote TEXT, served TEXT)")
    c.execute("CREATE TABLE cocktail_contents (cocktail_id INT, ingredient_id INT, amt_value REAL, amt_unit TEXT)")

    conn.close()

def store_all_data(all_cocktails_data, all_ingredients):
    if not os.path.exists(os.path.join(output_base_dir, "cocktails.db")):
        init_database()

    conn = sqlite3.connect(os.path.join(output_base_dir, "cocktails.db"))
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
            insert_string = 'INSERT INTO cocktail_contents VALUES ({0}, {1}, {2}, "{3}")'.format(cocktail_id,
                                                                                                  ingredient_id,
                                                                                                  amt_value,
                                                                                                  amt_unit)
            try:
                c.execute(insert_string)
            except sqlite3.OperationalError as e:
                print("sqlite3.OperationalError", e, "insert_string:", insert_string)
    conn.commit()


def launch_gui():
    conn = sqlite3.connect(os.path.join(output_base_dir, "cocktails.db"))
    c = conn.cursor()

    select_id_string = 'SELECT link_name, synonyms_csv FROM ingredients'
    c.execute(select_id_string)
    all_ingredients = c.fetchall()
    display_ingredients = [tup[0] for tup in all_ingredients]  # [tup[1] for tup in all_ingredients]

    sg.theme('DarkAmber')  # Add a touch of color
    # All the stuff inside your window.
    layout = [[sg.Text('Select an ingredient')],
              # [sg.Text('Enter something on Row 2'), sg.InputText()],
              [sg.Button('Ok'), sg.Button('Cancel')],
              [sg.Combo(display_ingredients)]]

    # Create the Window
    window = sg.Window('Booze Browser', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        print("event", event)
        print("values", values)
        if event in (None, 'Cancel'):  # if user closes window or clicks cancel
            break
        print('You entered ', values[0])
        chosen_ingredient = values[0]
        get_ing_id_str = 'SELECT ingredient_id FROM ingredients WHERE link_name = "{0}"'.format(chosen_ingredient)
        c.execute(get_ing_id_str)
        ingredient_id = c.fetchone()[0]
        get_matching_cocktails_str = 'SELECT cocktails.link_name FROM cocktails, cocktail_contents WHERE cocktail_contents.cocktail_id = cocktails.cocktail_id AND cocktail_contents.ingredient_id = {0}'.format(ingredient_id)
        c.execute(get_matching_cocktails_str)
        all_cocktails = c.fetchall()
        all_cocktails = [tup[0] for tup in all_cocktails]

        print(all_cocktails)

        choose_cocktail_layout = [[sg.Combo(all_cocktails)]]
        window2 = sg.Window("window 2", choose_cocktail_layout)
        event, values = window2.read()


    window.close()


# get_all_raw_text()
# all_cocktails_data, all_ingredients = parse_all_raw_text()
# store_all_data(all_cocktails_data, all_ingredients)
launch_gui()

