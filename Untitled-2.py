import sqlite3

def create_table():
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nesneler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nesne_adi TEXT,
            kayit_tarihi TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

def add_nesne(nesne_adi, kayit_tarihi):
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO nesneler (nesne_adi, kayit_tarihi) VALUES (?, ?)", (nesne_adi, kayit_tarihi))
    conn.commit()
    conn.close()

add_nesne("Kalem", "2021-01-01")
add_nesne("Defter", "2021-01-02")
add_nesne("Kitap", "2021-01-03")
add_nesne("Bilgisayar", "2021-01-04")

def get_all_nesneler():
    conn = sqlite3.connect('nesneler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nesneler")
    nesneler = cursor.fetchall()
    conn.close()
    return nesneler

def print_nesneler():
    nesneler = get_all_nesneler()
    for nesne in nesneler:
        print(nesne)

print_nesneler()