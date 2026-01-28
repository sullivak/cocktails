import os
import re
import urllib.request
import xml.etree.ElementTree as ET

from config import DATA_DIR


def get_all_raw_text():
    """Scrapes Wikipedia's Special:Export API for IBA cocktails, saves raw MediaWiki markup to text files."""
    base_url = "https://en.wikipedia.org/wiki/Special:Export/List_of_IBA_official_cocktails"
    output_dir = os.path.join(DATA_DIR, "cocktail_raw_txts")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    cocktail_url_template = "https://en.wikipedia.org/wiki/Special:Export/{0}"
    weird_prefix = "{http://www.mediawiki.org/xml/export-0.10/}"
    link_regex = re.compile(r"\[\[(.* ?)\]\]")
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


if __name__ == "__main__":
    get_all_raw_text()
