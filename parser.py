import os
import re
import glob

from config import DATA_DIR


def infobox_line_to_kv_pair(line):
    """Parse a line from a MediaWiki infobox into a key-value pair."""
    if "=" in line:
        parts = line.split("=")
        key = parts[0]
        value = "=".join(parts[1:])
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
    """Write ingredient data to a file for manual cleaning."""
    all_ingredients = set()
    for cocktail_name, cocktail_data in all_cocktails_data.items():
        print(cocktail_name)
        cocktail_ingredients = []
        for raw_ingredient in cocktail_data['ingredients_raw']:
            if raw_ingredient[0] == "|":
                raw_ingredient = raw_ingredient[1:]
            raw_ingredient = raw_ingredient.replace("ingredients =", "")
            raw_ingredient = raw_ingredient.replace("*", "")
            raw_ingredient = raw_ingredient.lstrip()

            amt_regex = r"([0-9]+(\.|\s)?[0-9]*\s?(cl|ml|dash|dashes|teaspoons|drops|splash)?)"
            match = re.search(amt_regex, raw_ingredient)
            if match is None:
                cocktail_ingredients.append({'amt': (raw_ingredient, "???"), 'ing': (raw_ingredient, "???")})
                all_ingredients.add((raw_ingredient, "???"))
            else:
                raw_amt = match.group(0)
                amt_quant_regex = r"([0-9]+(\.|\s)?[0-9]*)"
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
                linked_ing_regex = r"\[\[(.+)\]\]"
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
        all_cocktails_data[cocktail_name]['ingredients'] = cocktail_ingredients

    out_lines = []
    for cocktail_name, cocktail_data in all_cocktails_data.items():
        out_lines.append("###\n")
        out_lines.append(cocktail_name + "\n")
        for ingredient in cocktail_data['ingredients']:
            out_line = "amt: {0},{1}, ing: {2},{3}\n".format(
                ingredient['amt'][0], ingredient['amt'][1],
                ingredient['ing'][0], ingredient['ing'][1]
            )
            out_lines.append(out_line)

    with open(os.path.join(DATA_DIR, "cocktail_ings_to_clean.txt"), 'w') as fp:
        fp.writelines(out_lines)


def parse_all_raw_text():
    """Parse infobox data from raw files and read manually cleaned ingredient data."""
    in_dir = os.path.join(DATA_DIR, "cocktail_raw_txts")
    infobox_start = "{{Infobox cocktail"
    all_raw_paths = glob.glob(os.path.join(in_dir, "*.txt"))

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

    # Read manually cleaned ingredient data
    with open(os.path.join(DATA_DIR, "cocktail_ings_cleaned.txt"), 'r') as fp:
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
        clean_ingredients.append({
            'amt': (float(amt_quant.strip()), amt_measure.strip()),
            'ing': (ing_link, ing_name)
        })
        if ing_link in all_ingredients:
            all_ingredients[ing_link].add(ing_name)
        else:
            all_ingredients[ing_link] = {ing_name}

    return all_cocktails_data, all_ingredients


if __name__ == "__main__":
    cocktails, ingredients = parse_all_raw_text()
    print(f"Parsed {len(cocktails)} cocktails with {len(ingredients)} unique ingredients")
