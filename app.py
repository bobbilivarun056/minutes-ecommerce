import os
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configure where to save uploaded images locally
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect("minutes.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- ROUTES TO DISPLAY PAGES ---
@app.route('/')
def home(): return render_template('storefront.html')

@app.route('/admin')
def admin(): return render_template('admin.html')

@app.route('/cart')
def cart(): return render_template('basket.html')


# --- API ENDPOINTS ---

# 1. Get products
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = sqlite3.connect("minutes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(products)

# 2. Add product
@app.route('/api/products', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    file = request.files.get('image')
    image_path = "/static/uploads/placeholder.jpg"
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        image_path = f"/static/uploads/{file.filename}"
    conn = sqlite3.connect("minutes.db")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', (name, price, image_path))
    conn.commit()
    conn.close()
    return jsonify({"message": "Success!"}), 201

# 3. Fail-Safe Cloud Checkout API (Bypasses email blocks completely)
@app.route('/api/checkout', methods=['POST'])
def process_checkout():
    data = request.json
    cart_items = data.get('cart', [])
    address = data.get('address', '')
    total_price = data.get('total', 0)
    
    # Format the item list text and print directly to Render Dashboard Logs
    print("\n" + "="*40)
    print("📢 SUCCESS: MINUTES LIVE ORDER LOGGED ON CLOUD")
    print("="*40)
    for item in cart_items:
        print(f"📦 ITEM: {item['name']} - ₹{item['price']}")
    print(f"💰 TOTAL BILL: ₹{total_price}")
    print(f"📍 SHIPPING ADDRESS: {address}")
    print("="*40 + "\n")
    
    # Instantly returns success to the user interface
    return jsonify({"message": "Order processed successfully!"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
