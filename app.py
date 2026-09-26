import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message

app = Flask(__name__)

# --- MAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = '://gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'bobbilimighty@gmail.com'      
app.config['MAIL_PASSWORD'] = 'rrim hnrl clpz digq'       
app.config['MAIL_DEFAULT_SENDER'] = 'bobbilimighty@gmail.com'  

mail = Mail(app)

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

# 3. Process Checkout & Send Automated Customer Email (With Safe Fallback)
@app.route('/api/checkout', methods=['POST'])
def process_checkout():
    data = request.json
    cart_items = data.get('cart', [])
    address = data.get('address', '')
    customer_email = data.get('email', '')  # Captures customer email parameter from frontend
    total_price = data.get('total', 0)
    
    # Format the item list text for the email body
    items_text = ""
    for item in cart_items:
        items_text += f"- {item['name']}: ₹{item['price']}\n"
        
    # Construct the Automated Transaction Email Message
    msg = Message(
        subject="Minutes E-Commerce - Order Confirmed! 🎉🛒",
        recipients=['bobbilimighty@gmail.com', customer_email],  # Sends copy to both you and the buyer!
        body=f"Hello,\n\nThank you for shopping on Minutes! Your order has been successfully placed via Cash on Delivery (COD).\n\n"
             f"📦 ORDER INVOICE SUMMARY:\n{items_text}\n"
             f"💰 Total Amount to Pay: ₹{total_price}\n\n"
             f"📍 SHIPPING LOCATION:\n{address}\n\n"
             f"Your items will arrive within 30 Minutes. Thank you for choosing Minutes Explore Plus!"
    )
    
    # Instantly print order to Render Dashboard Logs using flush=True
    print("\n" + "="*40, flush=True)
    print("📢 AUTOMATED INVOICE INBOUND PROCESS STARTED", flush=True)
    print(f"📧 TARGET CUSTOMER EMAIL: {customer_email}", flush=True)
    print(f"💰 BILL TOTAL: ₹{total_price}", flush=True)
    print(f"📍 SHIP LOCATION: {address}", flush=True)
    print("="*40 + "\n", flush=True)
    
    try:
        mail.send(msg)
        print(f"📨 Success: Automated email confirmation dispatched to {customer_email}!", flush=True)
        return jsonify({"message": "Order processed and email sent successfully!"}), 200
    except Exception as e:
        # Robust Fallback Safety Net: If the Render cloud infrastructure network blocks or delays the SMTP port,
        # it prints the log here but STILL returns a successful 200 message to prevent the front-end page from freezing.
        print(f"⚠️ Email Dispatch Network Alert: {str(e)}", flush=True)
        print("🚀 Safeguard Override: Bypassing mail blocker to keep button responsive.", flush=True)
        return jsonify({"message": "Order processed successfully (Local Offline Mode)!"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
