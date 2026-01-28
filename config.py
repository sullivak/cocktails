import os

DATA_DIR = os.environ.get("COCKTAILS_DATA_DIR", "/home/sullivak/Data/Cocktails")
DB_PATH = os.path.join(DATA_DIR, "cocktails.db")
