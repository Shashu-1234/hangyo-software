import sqlite3
import os
import hashlib
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hangyo_data.db")
APP_DIR = os.path.dirname(os.path.abspath(__file__))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        full_name TEXT DEFAULT ''
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        price REAL NOT NULL DEFAULT 0,
        stock_qty REAL DEFAULT 0,
        low_stock_alert INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        owner_name TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        address TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        credit_limit REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT UNIQUE NOT NULL,
        shop_id INTEGER NOT NULL,
        order_date TEXT DEFAULT (date('now')),
        due_date TEXT DEFAULT '',
        total_amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        delivery_status TEXT DEFAULT 'Pending',
        notes TEXT DEFAULT '',
        FOREIGN KEY (shop_id) REFERENCES shops(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT DEFAULT (date('now')),
        notes TEXT DEFAULT '',
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS stock_receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT DEFAULT '',
        receipt_date TEXT DEFAULT (date('now')),
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS stock_receipt_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL DEFAULT 0,
        batch_no TEXT DEFAULT '',
        expiry_date TEXT DEFAULT '',
        FOREIGN KEY (receipt_id) REFERENCES stock_receipts(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS company_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_date TEXT DEFAULT (date('now')),
        status TEXT DEFAULT 'Draft',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS company_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        FOREIGN KEY (company_order_id) REFERENCES company_orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        shop_id INTEGER NOT NULL,
        return_date TEXT DEFAULT (date('now')),
        total_credit REAL DEFAULT 0,
        reason TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        FOREIGN KEY (shop_id) REFERENCES shops(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS return_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        condition TEXT DEFAULT 'Damaged',
        FOREIGN KEY (return_id) REFERENCES returns(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # Default admin
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                  ('admin', hash_password('admin123'), 'admin', 'Administrator'))

    # Sample products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample = [
            ('Mango Stick',       'Stick',   10.0, 100, 15),
            ('Chocolate Bar',     'Bar',     15.0,  80, 10),
            ('Vanilla Cup',       'Cup',     12.0,  60, 10),
            ('Strawberry Cone',   'Cone',    18.0,  50,  8),
            ('Butterscotch Bar',  'Bar',     15.0,  70, 10),
            ('Orange Candy',      'Candy',    5.0, 150, 20),
            ('Kesar Pista',       'Premium', 25.0,  30,  5),
            ('Choco Dip',         'Stick',   20.0,  45,  8),
        ]
        c.executemany(
            "INSERT INTO products (name,category,price,stock_qty,low_stock_alert) VALUES (?,?,?,?,?)",
            sample)

    # Sample shops
    c.execute("SELECT COUNT(*) FROM shops")
    if c.fetchone()[0] == 0:
        sample_shops = [
            ('Sharma General Store', 'Ravi Sharma',  '9876543210', 'MG Road, Block A', 'Trusted customer', 5000),
            ('Patel Ice Cream',      'Suresh Patel', '9988776655', 'Station Road',     'Cash only',        2000),
            ('City Cool Corner',     'Anita Desai',  '9123456789', 'Market Area',      '',                 3000),
        ]
        c.executemany(
            "INSERT INTO shops (name,owner_name,phone,address,notes,credit_limit) VALUES (?,?,?,?,?,?)",
            sample_shops)

    conn.commit()
    conn.close()


def verify_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, full_name FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'role': row[2], 'full_name': row[3]}
    return None


def get_next_bill_no():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    count = c.fetchone()[0] + 1
    conn.close()
    return f"BILL-{count:04d}"


def backup_database():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(APP_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    dest = os.path.join(backup_dir, f"hangyo_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def get_shop_outstanding(shop_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT COALESCE(SUM(total_amount - paid_amount), 0)
                 FROM orders WHERE shop_id=? AND status != 'Paid'""", (shop_id,))
    amt = c.fetchone()[0]
    conn.close()
    return amt


def row_to_dict(row):
    if row is None:
        return {}
    return dict(zip(row.keys(), tuple(row)))


def rows_to_dicts(rows):
    return [row_to_dict(r) for r in rows]
