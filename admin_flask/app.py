
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3
import hashlib
import os
from datetime import datetime
import json
from config import Config
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
config = Config()
app.secret_key = config.SECRET_KEY

# Upload configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom filter for date formatting
@app.template_filter('datetime')
def datetime_filter(value):
    """Convert string datetime to formatted date"""
    if not value:
        return 'N/A'
    try:
        if isinstance(value, str):
            from datetime import datetime
            # Try to parse the datetime string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        elif hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        else:
            return str(value)
    except:
        return str(value) if value else 'N/A'

def get_db_connection():
    """Get database connection"""
    try:
        connection = sqlite3.connect(config.DATABASE)
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as e:
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
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM bread_admin WHERE bread_admin_username = ?", (username,))
                admin = cursor.fetchone()
                
                if admin and admin['bread_admin_password']:
                    stored_password = admin['bread_admin_password']
                    
                    md5_hash = hashlib.md5(password.encode()).hexdigest()
                    
                    if stored_password == md5_hash or stored_password == password:  # Also allow plain text for testing
                        session['admin_id'] = admin['bread_admin_id']
                        session['admin_username'] = admin['bread_admin_username']
                        flash('Login successful!', 'success')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Invalid username or password!', 'error')
                else:
                    flash('Invalid username or password!', 'error')
            except sqlite3.Error as e:
                flash(f'Database error: {str(e)}', 'error')
            
            cursor.close()
            conn.close()
        else:
            flash('Database connection failed!', 'error')
    
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
        
        try:
            cursor.execute("SELECT COUNT(*) FROM bread_users")
            result = cursor.fetchone()
            stats['total_users'] = result[0] if result else 0
        except sqlite3.Error:
            stats['total_users'] = 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM bread_items")
            result = cursor.fetchone()
            stats['total_items'] = result[0] if result else 0
        except sqlite3.Error:
            stats['total_items'] = 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM bread_orders")
            result = cursor.fetchone()
            stats['total_orders'] = result[0] if result else 0
        except sqlite3.Error:
            stats['total_orders'] = 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM bread_orders WHERE bread_order_status = 'pending'")
            result = cursor.fetchone()
            stats['pending_orders'] = result[0] if result else 0
        except sqlite3.Error:
            stats['pending_orders'] = 0
        
        cursor.close()
        conn.close()
    
    return render_template('dashboard.html', stats=stats)

@app.route('/api/chart/orders')
def chart_orders():
    """Get order data for charts"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Get orders by date for the last 7 days
            cursor.execute("""
                SELECT DATE(bread_order_created_at) as order_date, COUNT(*) as count, SUM(bread_order_total) as total
                FROM bread_orders 
                WHERE bread_order_created_at >= date('now', '-7 days')
                GROUP BY DATE(bread_order_created_at)
                ORDER BY order_date
            """)
            orders = cursor.fetchall()
            
            # Get orders by status
            cursor.execute("""
                SELECT bread_order_status, COUNT(*) as count
                FROM bread_orders
                GROUP BY bread_order_status
            """)
            status_data = cursor.fetchall()
            
            chart_data = {
                'daily_orders': [{'date': order['order_date'], 'count': order['count'], 'total': order['total']} for order in orders],
                'status_distribution': [{'status': status['bread_order_status'], 'count': status['count']} for status in status_data]
            }
            
            return jsonify(chart_data)
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/api/chart/items')
def chart_items():
    """Get item data for charts"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Get items by type
            cursor.execute("""
                SELECT bread_item_type, COUNT(*) as count
                FROM bread_items
                GROUP BY bread_item_type
            """)
            items = cursor.fetchall()
            
            chart_data = {
                'items_by_type': [{'type': item['bread_item_type'], 'count': item['count']} for item in items]
            }
            
            return jsonify(chart_data)
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/users')
def users():
    """View all users"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    users_list = []
    
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM bread_users ORDER BY bread_user_id DESC")
            users_list = cursor.fetchall()
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            users_list = []
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
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM bread_items ORDER BY bread_item_id DESC")
            items_list = cursor.fetchall()
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            items_list = []
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
        
        # Handle image upload
        item_image = 'default-item.jpg'  # Default image
        if 'item_image' in request.files:
            file = request.files['item_image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Create unique filename
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Create upload directory if it doesn't exist
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                try:
                    file.save(file_path)
                    item_image = filename
                except Exception as e:
                    flash(f'Error uploading image: {str(e)}', 'error')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO bread_items (bread_item_name, bread_item_description, bread_item_price, bread_item_type, bread_item_image, bread_item_created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item_name, item_description, item_price, item_type, item_image, datetime.now()))
                
                conn.commit()
                flash('Item added successfully!', 'success')
                return redirect(url_for('items'))
            except sqlite3.Error as e:
                flash(f'Database error: {str(e)}', 'error')
            
            cursor.close()
            conn.close()
    
    return render_template('add_item.html')

@app.route('/items/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    """Edit existing item"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    item = None
    
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM bread_items WHERE bread_item_id = ?", (item_id,))
            item = cursor.fetchone()
            
            if request.method == 'POST' and item:
                item_name = request.form['item_name']
                item_description = request.form['item_description']
                item_price = float(request.form['item_price'])
                item_type = request.form['item_type']
                item_image = request.form['item_image']
                
                cursor.execute("""
                    UPDATE bread_items 
                    SET bread_item_name = ?, bread_item_description = ?, bread_item_price = ?, 
                        bread_item_type = ?, bread_item_image = ?, bread_item_updated_at = ?
                    WHERE bread_item_id = ?
                """, (item_name, item_description, item_price, item_type, item_image, datetime.now(), item_id))
                
                conn.commit()
                flash('Item updated successfully!', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('items'))
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
        
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
        try:
            cursor.execute("DELETE FROM bread_items WHERE bread_item_id = ?", (item_id,))
            conn.commit()
            flash('Item deleted successfully!', 'success')
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
        cursor.close()
        conn.close()
    
    return redirect(url_for('items'))

@app.route('/orders')
def orders():
    """View all orders"""
    if not check_auth():
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    orders_list = []
    
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT o.*, u.bread_user_name as username, u.bread_user_email as email 
                FROM bread_orders o 
                LEFT JOIN bread_users u ON o.bread_user_id = u.bread_user_id 
                ORDER BY o.bread_order_created_at DESC
            """)
            orders_list = cursor.fetchall()
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            orders_list = []
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
        try:
            cursor.execute("UPDATE bread_orders SET bread_order_status = ? WHERE bread_order_id = ?", (status, order_id))
            conn.commit()
            flash('Order status updated successfully!', 'success')
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
        cursor.close()
        conn.close()
    
    return redirect(url_for('orders'))

# API Routes for Mobile App
@app.route('/api/login', methods=['POST'])
def api_login():
    """Mobile app login endpoint"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        if not phone or not password:
            return jsonify({'success': False, 'message': 'Phone and password are required'})
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Check if user exists and get user data
                cursor.execute("SELECT * FROM bread_users WHERE bread_user_phone = ?", (phone,))
                user = cursor.fetchone()
                
                if user and user['bread_user_password'] == password:
                    user_data = {
                        'user_id': user['bread_user_id'],
                        'name': user['bread_user_name'],
                        'email': user['bread_user_email'],
                        'phone': user['bread_user_phone'],
                        'is_verified': user['bread_user_is_verified']
                    }
                    return jsonify({'success': True, 'message': 'Login successful', 'user': user_data})
                else:
                    return jsonify({'success': False, 'message': 'Invalid phone or password'})
            
            except sqlite3.Error as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/register', methods=['POST'])
def api_register():
    """Mobile app registration endpoint"""
    try:
        data = request.get_json()
        name = data.get('name')
        password = data.get('password')
        phone = data.get('phone')
        
        if not all([name, password, phone]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Check if user already exists
                cursor.execute("SELECT * FROM bread_users WHERE bread_user_phone = ?", (phone,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return jsonify({'success': False, 'message': 'User already exists with this phone'})
                
                # Insert new user
                cursor.execute("""
                    INSERT INTO bread_users (bread_user_name, bread_user_password, bread_user_phone, bread_user_created_at)
                    VALUES (?, ?, ?, ?)
                """, (name, password, phone, datetime.now()))
                
                conn.commit()
                user_id = cursor.lastrowid
                
                user_data = {
                    'user_id': user_id,
                    'name': name,
                    'phone': phone,
                    'is_verified': 0
                }
                
                return jsonify({'success': True, 'message': 'Registration successful', 'user': user_data})
            
            except sqlite3.Error as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/fetch_items', methods=['GET'])
def api_fetch_items():
    """Fetch menu items for mobile app"""
    try:
        item_type = request.args.get('item_type')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                if item_type and item_type != 'All':
                    cursor.execute("SELECT * FROM bread_items WHERE bread_item_type = ? ORDER BY bread_item_id DESC", (item_type,))
                else:
                    cursor.execute("SELECT * FROM bread_items ORDER BY bread_item_id DESC")
                
                items = cursor.fetchall()
                items_list = []
                
                for item in items:
                    items_list.append({
                        'id': item['bread_item_id'],
                        'name': item['bread_item_name'],
                        'description': item['bread_item_description'],
                        'price': item['bread_item_price'],
                        'type': item['bread_item_type'],
                        'image': item['bread_item_image'],
                        'created_at': item['bread_item_created_at']
                    })
                
                return jsonify({'success': True, 'items': items_list})
            
            except sqlite3.Error as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/add_order', methods=['POST'])
def api_add_order():
    """Add order from mobile app"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        total = data.get('total')
        items = data.get('items', [])
        
        if not user_id or not total:
            return jsonify({'success': False, 'message': 'User ID and total are required'})
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Insert order
                cursor.execute("""
                    INSERT INTO bread_orders (bread_user_id, bread_order_total, bread_order_status, bread_order_created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, total, 'pending', datetime.now()))
                
                conn.commit()
                order_id = cursor.lastrowid
                
                return jsonify({'success': True, 'message': 'Order placed successfully', 'order_id': order_id})
            
            except sqlite3.Error as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/get_orders', methods=['GET'])
def api_get_orders():
    """Get orders for mobile app"""
    try:
        user_id = request.args.get('user_id')
        order_id = request.args.get('order_id')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                if order_id:
                    # Get specific order
                    cursor.execute("""
                        SELECT o.*, u.bread_user_name as user_name, u.bread_user_email as user_email 
                        FROM bread_orders o 
                        LEFT JOIN bread_users u ON o.bread_user_id = u.bread_user_id 
                        WHERE o.bread_order_id = ?
                    """, (order_id,))
                    order = cursor.fetchone()
                    
                    if order:
                        order_data = {
                            'order_id': order['bread_order_id'],
                            'user_id': order['bread_user_id'],
                            'user_name': order['user_name'],
                            'user_email': order['user_email'],
                            'total': order['bread_order_total'],
                            'status': order['bread_order_status'],
                            'created_at': order['bread_order_created_at']
                        }
                        return jsonify({'success': True, 'order': order_data})
                    else:
                        return jsonify({'success': False, 'message': 'Order not found'})
                
                elif user_id:
                    # Get orders for specific user
                    cursor.execute("""
                        SELECT * FROM bread_orders 
                        WHERE bread_user_id = ? 
                        ORDER BY bread_order_created_at DESC
                    """, (user_id,))
                    orders = cursor.fetchall()
                    orders_list = []
                    
                    for order in orders:
                        orders_list.append({
                            'order_id': order['bread_order_id'],
                            'user_id': order['bread_user_id'],
                            'total': order['bread_order_total'],
                            'status': order['bread_order_status'],
                            'created_at': order['bread_order_created_at']
                        })
                    
                    return jsonify({'success': True, 'orders': orders_list})
                else:
                    return jsonify({'success': False, 'message': 'User ID or Order ID is required'})
            
            except sqlite3.Error as e:
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

# Static file serving for mobile app images
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files for mobile app"""
    return send_from_directory('static', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    """Serve image files for mobile app"""
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
