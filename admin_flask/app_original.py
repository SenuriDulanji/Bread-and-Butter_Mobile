from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import hashlib
import os
from datetime import datetime
import json
from config import Config

app = Flask(__name__)
config = Config()
app.secret_key = config.SECRET_KEY

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**config.DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def check_auth():
    """Check if admin is authenticated"""
    return 'admin_id' in session

@app.route('/')
def index():
    """Redirect to login if not authenticated, otherwise to dashboard"""
    if check_auth():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bread_admin WHERE bread_admin_username = %s", (username,))
            admin = cursor.fetchone()
            
            if admin and admin['bread_admin_password'] == hashlib.md5(password.encode()).hexdigest():
                session['admin_id'] = admin['bread_admin_id']
                session['admin_username'] = admin['bread_admin_username']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'error')
            
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    stats = {
        'total_users': 0,
        'total_items': 0,
        'total_orders': 0,
        'pending_orders': 0
    }
    
    if conn:
        cursor = conn.cursor()
        
        # Get total users
        cursor.execute("SELECT COUNT(*) FROM bread_users")
        stats['total_users'] = cursor.fetchone()[0]
        
        # Get total items
        cursor.execute("SELECT COUNT(*) FROM bread_items")
        stats['total_items'] = cursor.fetchone()[0]
        
        # Get total orders
        cursor.execute("SELECT COUNT(*) FROM bread_orders")
        stats['total_orders'] = cursor.fetchone()[0]
        
        # Get pending orders
        cursor.execute("SELECT COUNT(*) FROM bread_orders WHERE order_status = 'pending'")
        stats['pending_orders'] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
    
    return render_template('dashboard.html', stats=stats)

@app.route('/users')
def users():
    """View all users"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    users_list = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bread_users ORDER BY created_at DESC")
        users_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('users.html', users=users_list)

@app.route('/items')
def items():
    """View all items"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    items_list = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bread_items ORDER BY created_at DESC")
        items_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('items.html', items=items_list)

@app.route('/items/add', methods=['GET', 'POST'])
def add_item():
    """Add new item"""
    if not check_auth():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_description = request.form['item_description']
        item_price = float(request.form['item_price'])
        item_type = request.form['item_type']
        item_image = request.form['item_image']  # URL or filename
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bread_items (item_name, item_description, item_price, item_type, item_image, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (item_name, item_description, item_price, item_type, item_image, datetime.now()))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Item added successfully!', 'success')
            return redirect(url_for('items'))
    
    return render_template('add_item.html')

@app.route('/items/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    """Edit existing item"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    item = None
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bread_items WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        
        if request.method == 'POST' and item:
            item_name = request.form['item_name']
            item_description = request.form['item_description']
            item_price = float(request.form['item_price'])
            item_type = request.form['item_type']
            item_image = request.form['item_image']
            
            cursor.execute("""
                UPDATE bread_items 
                SET item_name = %s, item_description = %s, item_price = %s, 
                    item_type = %s, item_image = %s, updated_at = %s
                WHERE item_id = %s
            """, (item_name, item_description, item_price, item_type, item_image, datetime.now(), item_id))
            
            conn.commit()
            flash('Item updated successfully!', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('items'))
        
        cursor.close()
        conn.close()
    
    if not item:
        flash('Item not found!', 'error')
        return redirect(url_for('items'))
    
    return render_template('edit_item.html', item=item)

@app.route('/items/delete/<int:item_id>')
def delete_item(item_id):
    """Delete item"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bread_items WHERE item_id = %s", (item_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Item deleted successfully!', 'success')
    
    return redirect(url_for('items'))

@app.route('/orders')
def orders():
    """View all orders"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    orders_list = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, u.username, u.email 
            FROM bread_orders o 
            LEFT JOIN bread_users u ON o.user_id = u.user_id 
            ORDER BY o.created_at DESC
        """)
        orders_list = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('orders.html', orders=orders_list)

@app.route('/orders/update_status/<int:order_id>/<status>')
def update_order_status(order_id, status):
    """Update order status"""
    if not check_auth():
        return redirect(url_for('login'))
    
    valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
    if status not in valid_statuses:
        flash('Invalid status!', 'error')
        return redirect(url_for('orders'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE bread_orders SET order_status = %s WHERE order_id = %s", (status, order_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Order status updated successfully!', 'success')
    
    return redirect(url_for('orders'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)