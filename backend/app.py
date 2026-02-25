from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt
import os
from datetime import datetime, timedelta
import secrets
import json
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import pandas as pd
import numpy as np
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')
from flask import Flask, jsonify, request
# Import the function we created earlier
from app.services.ai_service import get_recommendation_json 
# Assuming you use flask_jwt_extended for the "Bearer token" logic
from flask_jwt_extended import jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breadandbutter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_ALGORITHM'] = 'HS256'


# Image upload configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'uploads/images'

@app.route('/api/recommendations', methods=['GET'])
@jwt_required() # Protects the route so only logged-in users can access
def recommendations():
    try:
        # 1. Get the User ID from the token (Frontend sends 'Bearer <token>')
        current_user_id = get_jwt_identity() 
        
        # 2. Call your AI Service
        # Note: get_recommendation_json returns a JSON string, so we parse it first
        import json
        ai_response_text = get_recommendation_json(current_user_id)
        ai_data = json.loads(ai_response_text)
        
        # 3. Send it back to Flutter
        return jsonify(ai_data), 200

    except Exception as e:
        print(f"Error in recommendation route: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(file, max_size=(800, 600)):
    """Process uploaded image: resize and optimize"""
    try:
        # Open and process the image
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize image while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        return img
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expires = db.Column(db.DateTime, nullable=True)
    loyalty_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.phone}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    discount_percentage = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('Category', backref=db.backref('menu_items', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image': self.image,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'is_available': self.is_available,
            'discount_percentage': self.discount_percentage,
            'discounted_price': self.price * (1 - self.discount_percentage / 100) if self.discount_percentage > 0 else self.price
        }
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, preparing, ready, delivered
    delivery_address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    items = db.Column(db.Text, nullable=False)  # JSON string of ordered items
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    def get_items(self):
        return json.loads(self.items) if self.items else []
    
    def set_items(self, items_list):
        self.items = json.dumps(items_list)
    
    def __repr__(self):
        return f'<Order {self.id}>'

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    discount_percentage = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image': self.image,
            'discount_percentage': self.discount_percentage,
            'is_active': self.is_active,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None
        }
    
    def __repr__(self):
        return f'<Offer {self.title}>'

# Helper function to get stats
def get_stats():
    return {
        'total_users': User.query.count(),
        'total_orders': Order.query.count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_amount)).scalar() or 0,
        'total_menu_items': MenuItem.query.count()
    }

# Web Interface Routes
@app.route('/')
def dashboard():
    # Get statistics for dashboard
    stats = get_stats()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', stats=stats, recent_orders=recent_orders)

@app.route('/users')
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    stats = get_stats()
    return render_template('users.html', users=users_list, stats=stats)

@app.route('/menu')
def menu():
    menu_items = MenuItem.query.order_by(MenuItem.created_at.desc()).all()
    categories = Category.query.all()
    stats = get_stats()
    return render_template('menu.html', menu_items=menu_items, categories=categories, stats=stats)

@app.route('/orders')
def orders():
    # Get page number from query parameters, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Show 50 orders per page
    
    # Get status filter from query parameters
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Build base query
    query = Order.query
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Apply search filter if provided
    if search_query:
        query = query.join(User).filter(
            db.or_(
                Order.id.like(f'%{search_query}%'),
                Order.delivery_address.like(f'%{search_query}%'),
                Order.phone.like(f'%{search_query}%'),
                User.name.like(f'%{search_query}%')
            )
        )
    
    # Order by creation date (newest first) and paginate
    orders_pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    orders_list = orders_pagination.items
    stats = get_stats()
    
    return render_template('orders.html', 
                         orders=orders_list, 
                         stats=stats,
                         pagination=orders_pagination,
                         current_page=page,
                         status_filter=status_filter,
                         search_query=search_query)

@app.route('/offers')
def offers():
    offers_list = Offer.query.order_by(Offer.created_at.desc()).all()
    stats = get_stats()
    return render_template('offers.html', offers=offers_list, stats=stats)

# Web API Routes (for the web interface)
@app.route('/api/users/<int:user_id>')
def get_user_details(user_id):
    user = User.query.get_or_404(user_id)
    orders_count = Order.query.filter_by(user_id=user_id).count()
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'email': user.email,
            'is_verified': user.is_verified,
            'loyalty_points': user.loyalty_points,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'orders_count': orders_count
    })

@app.route('/api/users/<int:user_id>/verify', methods=['POST'])
def verify_user_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'User verified successfully'
    })

@app.route('/api/users/<int:user_id>/loyalty-points', methods=['PUT'])
def update_user_loyalty_points(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    user.loyalty_points = data.get('loyalty_points', user.loyalty_points)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Loyalty points updated successfully'
    })

@app.route('/api/menu-items/<int:item_id>')
def get_menu_item_details(item_id):
    item = MenuItem.query.get_or_404(item_id)
    
    return jsonify({
        'success': True,
        'item': item.to_dict()
    })

@app.route('/api/menu-items', methods=['POST'])
def create_menu_item():
    try:
        # Handle form data (including file upload)
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = float(request.form.get('price'))
        discount_percentage = float(request.form.get('discount_percentage', 0))
        category_id = int(request.form.get('category_id'))
        is_available = request.form.get('is_available') == 'true'
        
        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4()}.{file_extension}"
                
                # Create upload directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Process and save image
                processed_img = process_image(file)
                if processed_img:
                    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                    processed_img.save(image_path, quality=85, optimize=True)
                    # Store just filename for database (we'll construct the URL in frontend)
                    # Don't change image_filename - it's already just the UUID.extension
        
        # Create menu item
        item = MenuItem(
            name=name,
            description=description,
            price=price,
            discount_percentage=discount_percentage,
            category_id=category_id,
            is_available=is_available,
            image=image_filename
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Menu item created successfully',
            'item_id': item.id,
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating menu item: {str(e)}'
        }), 400

@app.route('/api/menu-items/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    try:
        item = MenuItem.query.get_or_404(item_id)
        
        # Handle form data (including file upload)
        if request.form:
            # Form data (with potential file upload)
            name = request.form.get('name', item.name)
            description = request.form.get('description', item.description)
            price = float(request.form.get('price', item.price))
            discount_percentage = float(request.form.get('discount_percentage', item.discount_percentage))
            category_id = int(request.form.get('category_id', item.category_id))
            is_available = request.form.get('is_available', 'true') == 'true'
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old image if exists
                    if item.image and os.path.exists(item.image):
                        try:
                            os.remove(item.image)
                        except OSError:
                            pass
                    
                    # Generate unique filename
                    file_extension = file.filename.rsplit('.', 1)[1].lower()
                    image_filename = f"{uuid.uuid4()}.{file_extension}"
                    
                    # Create upload directory if it doesn't exist
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    # Process and save image
                    processed_img = process_image(file)
                    if processed_img:
                        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                        processed_img.save(image_path, quality=85, optimize=True)
                        # Store just filename for database
                        item.image = image_filename
        else:
            # JSON data (no file upload)
            data = request.get_json()
            name = data.get('name', item.name)
            description = data.get('description', item.description)
            price = data.get('price', item.price)
            discount_percentage = data.get('discount_percentage', item.discount_percentage)
            category_id = data.get('category_id', item.category_id)
            is_available = data.get('is_available', item.is_available)
        
        # Update item fields
        item.name = name
        item.description = description
        item.price = price
        item.discount_percentage = discount_percentage
        item.category_id = category_id
        item.is_available = is_available
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Menu item updated successfully',
            'item': item.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating menu item: {str(e)}'
        }), 400

@app.route('/api/menu-items/<int:item_id>/availability', methods=['PUT'])
def toggle_menu_item_availability(item_id):
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    
    item.is_available = data.get('is_available', not item.is_available)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Item availability updated successfully'
    })

@app.route('/api/menu-items/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Menu item deleted successfully'
    })

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    order.status = data.get('status', order.status)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order status updated successfully'
    })

@app.route('/api/orders/<int:order_id>')
def get_order_details(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Get order items with menu item details
    order_items = order.get_items()
    enriched_items = []
    
    for item in order_items:
        # Try to get menu item details if item_id exists
        menu_item = None
        if 'item_id' in item:
            menu_item = MenuItem.query.get(item['item_id'])
        
        # Use menu item name if available, otherwise use the name from order item
        item_name = menu_item.name if menu_item else item.get('name', 'Unknown Item')
        
        enriched_item = {
            'item_id': item.get('item_id'),
            'name': item_name,
            'quantity': item.get('quantity', 1),
            'price': item.get('price', 0.0),
            'total': item.get('total', item.get('price', 0.0) * item.get('quantity', 1)),
            'menu_item': {
                'name': menu_item.name if menu_item else item.get('name', 'Unknown Item'),
                'description': menu_item.description if menu_item else None,
                'image': menu_item.image if menu_item else None,
                'category_name': menu_item.category.name if menu_item and menu_item.category else None
            } if menu_item else None
        }
        enriched_items.append(enriched_item)
    
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'user_id': order.user_id,
            'total_amount': order.total_amount,
            'status': order.status,
            'delivery_address': order.delivery_address,
            'phone': order.phone,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'items': enriched_items,
            'user': {
                'id': order.user.id,
                'name': order.user.name,
                'phone': order.user.phone,
                'email': order.user.email,
                'loyalty_points': order.user.loyalty_points
            } if order.user else None
        }
    })

# Mobile API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'success': False, 'message': 'Phone and password are required'}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password):
        return jsonify({'success': False, 'message': 'Invalid phone or password'}), 401
    
    if not user.is_verified:
        return jsonify({'success': False, 'message': 'Please verify your account first'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': access_token,
        'user': {
            'id': user.id,
            'phone': user.phone,
            'name': user.name,
            'email': user.email,
            'loyalty_points': user.loyalty_points
        }
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    name = data.get('name', '')
    email = data.get('email', '')
    
    if not phone or not password:
        return jsonify({'success': False, 'message': 'Phone and password are required'}), 400
    
    existing_user = User.query.filter_by(phone=phone).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Phone number already registered'}), 400
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    otp = str(secrets.randbelow(999999)).zfill(6)
    
    user = User(
        phone=phone,
        password=hashed_password,
        name=name,
        email=email,
        otp=otp,
        otp_expires=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Registration successful. Please verify your account.',
        'otp': otp  # In production, send via SMS
    })

@app.route('/api/verify', methods=['POST'])
def verify_otp():
    data = request.get_json()
    phone = data.get('phone')
    otp = data.get('otp')
    
    if not phone or not otp:
        return jsonify({'success': False, 'message': 'Phone and OTP are required'}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if user.otp != otp or (user.otp_expires and user.otp_expires < datetime.utcnow()):
        return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
    
    user.is_verified = True
    user.otp = None
    user.otp_expires = None
    db.session.commit()
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'success': True,
        'message': 'Account verified successfully',
        'token': access_token,
        'user': {
            'id': user.id,
            'phone': user.phone,
            'name': user.name,
            'email': user.email,
            'loyalty_points': user.loyalty_points
        }
    })

@app.route('/api/resend_otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'success': False, 'message': 'Phone is required'}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    otp = str(secrets.randbelow(999999)).zfill(6)
    user.otp = otp
    user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'OTP sent successfully',
        'otp': otp  # In production, send via SMS
    })

@app.route('/api/fetch_items', methods=['GET'])
def fetch_items():
    category_id = request.args.get('category_id')
    item_type = request.args.get('item_type')
    search = request.args.get('search', '')
    
    query = MenuItem.query.filter_by(is_available=True)
    
    # Handle category_id parameter (numeric)
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Handle item_type parameter (text-based like "Food", "Beverage")
    if item_type and item_type != "All":
        category = Category.query.filter_by(name=item_type).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    if search:
        query = query.filter(MenuItem.name.contains(search))
    
    items = query.all()
    categories = Category.query.all()
    
    return jsonify({
        'success': True,
        'items': [item.to_dict() for item in items],
        'categories': [{'id': cat.id, 'name': cat.name, 'image': cat.image} for cat in categories]
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify({
            'success': True,
            'categories': [{'id': cat.id, 'name': cat.name, 'image': cat.image} for cat in categories]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching categories: {str(e)}'}), 500

@app.route('/api/add_order', methods=['POST'])
@jwt_required()
def add_order():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    items = data.get('items', [])
    total_amount = data.get('total_amount', 0)
    delivery_address = data.get('delivery_address', '')
    phone = data.get('phone', '')
    
    if not items:
        return jsonify({'success': False, 'message': 'Items are required'}), 400
    
    order = Order(
        user_id=user_id,
        total_amount=total_amount,
        delivery_address=delivery_address,
        phone=phone,
        items=json.dumps(items)
    )
    
    db.session.add(order)
    
    # Add loyalty points (1 point per dollar)
    user = User.query.get(user_id)
    if user:
        user.loyalty_points += int(total_amount)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order placed successfully',
        'order_id': order.id
    })

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Delete the order
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting order: {str(e)}'
        }), 500

@app.route('/api/cleanup-database', methods=['POST'])
def cleanup_database():
    """Clean all data from the database - USE WITH CAUTION!"""
    try:
        # Delete all orders first (due to foreign key constraints)
        Order.query.delete()
        
        # Delete all menu items
        MenuItem.query.delete()
        
        # Delete all users
        User.query.delete()
        
        # Delete all categories
        Category.query.delete()
        
        # Delete all offers
        Offer.query.delete()
        
        # Commit all deletions
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Database cleaned successfully. All orders, menu items, users, categories, and offers have been removed.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cleaning database: {str(e)}'
        }), 500

@app.route('/api/get_orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    orders_data = []
    for order in orders:
        # Get order items with menu item details (similar to get_order_details)
        order_items = order.get_items()
        enriched_items = []
        
        for item in order_items:
            # Try to get menu item details if item_id exists
            menu_item = None
            if 'item_id' in item:
                menu_item = MenuItem.query.get(item['item_id'])
            
            # Use menu item name if available, otherwise use the name from order item
            item_name = menu_item.name if menu_item else item.get('name', 'Unknown Item')
            
            enriched_item = {
                'item_id': item.get('item_id'),
                'name': item_name,
                'quantity': item.get('quantity', 1),
                'price': item.get('price', 0.0),
                'total': item.get('total', item.get('price', 0.0) * item.get('quantity', 1)),
                'image': menu_item.image if menu_item else None,
                'description': menu_item.description if menu_item else None,
                'category_name': menu_item.category.name if menu_item and menu_item.category else None
            }
            enriched_items.append(enriched_item)
        
        orders_data.append({
            'id': order.id,
            'total_amount': order.total_amount,
            'status': order.status,
            'delivery_address': order.delivery_address,
            'items': enriched_items,
            'created_at': order.created_at.isoformat()
        })
    
    return jsonify({
        'success': True,
        'orders': orders_data
    })

@app.route('/api/get_loyalty_points', methods=['GET'])
@jwt_required()
def get_loyalty_points():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'loyalty_points': user.loyalty_points
    })

@app.route('/api/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get personalized menu recommendations for the authenticated user"""
    try:
        user_id = int(get_jwt_identity())
        
        # Get user's order history
        user_orders = Order.query.filter_by(user_id=user_id).all()
        orders_data = []
        
        for order in user_orders:
            orders_data.append({
                'user_id': order.user_id,
                'items': order.items,
                'created_at': order.created_at.isoformat(),
                'total_amount': order.total_amount
            })
        
        # Get all menu items
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        menu_items_data = [item.to_dict() for item in menu_items]
        
        # Get all orders for collaborative filtering
        all_orders = Order.query.all()
        all_orders_data = []
        
        for order in all_orders:
            all_orders_data.append({
                'user_id': order.user_id,
                'items': order.items,
                'created_at': order.created_at.isoformat(),
                'total_amount': order.total_amount
            })
        
        # Generate recommendations
        if len(user_orders) > 0:
            # Personalized recommendations based on user history
            recommendations = recommendation_engine.get_recommendations(
                user_id, all_orders_data, menu_items_data, num_recommendations=3
            )
        else:
            # For new users, show trending items
            recommendations = recommendation_engine.get_trending_items(
                all_orders_data, menu_items_data, days=30, limit=3
            )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'user_has_history': len(user_orders) > 0,
            'recommendation_type': 'personalized' if len(user_orders) > 0 else 'trending'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating recommendations: {str(e)}'
        }), 500

@app.route('/api/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations_for_user(user_id):
    """Get recommendations for a specific user (admin endpoint)"""
    try:
        # Get user's order history
        user_orders = Order.query.filter_by(user_id=user_id).all()
        orders_data = []
        
        for order in user_orders:
            orders_data.append({
                'user_id': order.user_id,
                'items': order.items,
                'created_at': order.created_at.isoformat(),
                'total_amount': order.total_amount
            })
        
        # Get all menu items
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        menu_items_data = [item.to_dict() for item in menu_items]
        
        # Get all orders for collaborative filtering
        all_orders = Order.query.all()
        all_orders_data = []
        
        for order in all_orders:
            all_orders_data.append({
                'user_id': order.user_id,
                'items': order.items,
                'created_at': order.created_at.isoformat(),
                'total_amount': order.total_amount
            })
        
        # Generate recommendations
        if len(user_orders) > 0:
            recommendations = recommendation_engine.get_recommendations(
                user_id, all_orders_data, menu_items_data, num_recommendations=3
            )
        else:
            recommendations = recommendation_engine.get_trending_items(
                all_orders_data, menu_items_data, days=30, limit=3
            )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'user_id': user_id,
            'user_has_history': len(user_orders) > 0,
            'recommendation_type': 'personalized' if len(user_orders) > 0 else 'trending'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating recommendations: {str(e)}'
        }), 500

@app.route('/api/get_weekly_highlight', methods=['GET'])
def get_weekly_highlight():
    offers = Offer.query.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'offers': [offer.to_dict() for offer in offers]
    })

@app.route('/api/reset_pw', methods=['POST'])
def reset_password():
    data = request.get_json()
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'success': False, 'message': 'Phone is required'}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    otp = str(secrets.randbelow(999999)).zfill(6)
    user.otp = otp
    user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password reset OTP sent',
        'otp': otp  # In production, send via SMS
    })

@app.route('/api/verify_reset_pw', methods=['POST'])
def verify_reset_password():
    data = request.get_json()
    phone = data.get('phone')
    otp = data.get('otp')
    new_password = data.get('new_password')
    
    if not phone or not otp or not new_password:
        return jsonify({'success': False, 'message': 'Phone, OTP, and new password are required'}), 400
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if user.otp != otp or (user.otp_expires and user.otp_expires < datetime.utcnow()):
        return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
    
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    user.password = hashed_password
    user.otp = None
    user.otp_expires = None
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password reset successfully'
    })

# Forecasting API endpoints
@app.route('/api/forecast/data')
def get_forecast_data():
    """Generate order forecasting data using Prophet"""
    try:
        # Get historical order data grouped by date
        orders_query = """
        SELECT DATE(created_at) as order_date, COUNT(*) as order_count
        FROM "order" 
        WHERE created_at >= '2025-01-01' 
        GROUP BY DATE(created_at)
        ORDER BY order_date
        """
        
        # Execute raw SQL query
        result = db.session.execute(db.text(orders_query))
        
        # Convert to DataFrame
        data = []
        for row in result:
            data.append({'ds': datetime.strptime(row[0], '%Y-%m-%d'), 'y': row[1]})
        
        if not data:
            return jsonify({'success': False, 'message': 'No order data found'}), 404
        
        df = pd.DataFrame(data)
        
        # Create and train Prophet model
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,
            interval_width=0.95
        )
        
        model.fit(df)
        
        # Create future dataframe for 30 days
        future = model.make_future_dataframe(periods=30)
        
        # Make predictions
        forecast = model.predict(future)
        
        # Prepare response data
        historical_data = []
        for _, row in df.iterrows():
            historical_data.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'orders': int(row['y'])
            })
        
        forecast_data = []
        future_start = df['ds'].max() + timedelta(days=1)
        future_forecast = forecast[forecast['ds'] >= future_start].head(30)
        
        for _, row in future_forecast.iterrows():
            forecast_data.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted_orders': max(0, int(row['yhat'])),
                'lower_bound': max(0, int(row['yhat_lower'])),
                'upper_bound': max(0, int(row['yhat_upper']))
            })
        
        # Calculate summary statistics
        historical_avg = df['y'].mean()
        forecast_avg = future_forecast['yhat'].mean()
        growth_rate = ((forecast_avg - historical_avg) / historical_avg) * 100 if historical_avg > 0 else 0
        
        return jsonify({
            'success': True,
            'historical_data': historical_data,
            'forecast_data': forecast_data,
            'summary': {
                'historical_avg': round(historical_avg, 1),
                'forecast_avg': round(forecast_avg, 1),
                'growth_rate': round(growth_rate, 1),
                'total_historical_days': len(historical_data),
                'forecast_period_days': len(forecast_data)
            }
        })
        
    except Exception as e:
        print(f"Forecast error: {e}")
        return jsonify({'success': False, 'message': f'Error generating forecast: {str(e)}'}), 500


@app.route('/api/orders/analytics')
def get_orders_analytics():
    """Get comprehensive order analytics for dashboard"""
    try:
        # Basic statistics
        total_orders = Order.query.count()
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Status breakdown
        status_stats = {}
        for status in ['pending', 'confirmed', 'preparing', 'ready', 'delivered']:
            count = Order.query.filter_by(status=status).count()
            status_stats[status] = count
        
        # Daily orders in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_orders_query = """
        SELECT DATE(created_at) as order_date, COUNT(*) as count, SUM(total_amount) as revenue
        FROM "order" 
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY order_date
        """
        
        result = db.session.execute(db.text(daily_orders_query), {'start_date': thirty_days_ago})
        
        daily_stats = []
        for row in result:
            daily_stats.append({
                'date': row[0],
                'orders': row[1],
                'revenue': float(row[2])
            })
        
        # Top menu items
        top_items_query = """
        SELECT json_extract(items, '$[*].name') as item_names,
               json_extract(items, '$[*].quantity') as quantities,
               COUNT(*) as order_count
        FROM "order"
        GROUP BY json_extract(items, '$[*].name')
        ORDER BY order_count DESC
        LIMIT 10
        """
        
        # Weekly revenue trend
        weekly_revenue_query = """
        SELECT strftime('%Y-%W', created_at) as week,
               COUNT(*) as orders,
               SUM(total_amount) as revenue
        FROM "order"
        WHERE created_at >= date('now', '-8 weeks')
        GROUP BY strftime('%Y-%W', created_at)
        ORDER BY week
        """
        
        weekly_result = db.session.execute(db.text(weekly_revenue_query))
        weekly_stats = []
        for row in weekly_result:
            weekly_stats.append({
                'week': row[0],
                'orders': row[1],
                'revenue': float(row[2])
            })
        
        return jsonify({
            'success': True,
            'summary': {
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'avg_order_value': round(avg_order_value, 2),
                'status_breakdown': status_stats
            },
            'daily_stats': daily_stats,
            'weekly_stats': weekly_stats
        })
        
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({'success': False, 'message': f'Error getting analytics: {str(e)}'}), 500

# Static file serving for images
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/uploads/images/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create sample data if tables are empty
        if Category.query.count() == 0:
            categories = [
                Category(name='Burgers', image='burger.jpg'),
                Category(name='Pizza', image='pizza.jpg'),
                Category(name='Beverages', image='beverage.jpg'),
                Category(name='Desserts', image='dessert.jpg')
            ]
            for cat in categories:
                db.session.add(cat)
            
            db.session.commit()
            
            # Add sample menu items
            burger_cat = Category.query.filter_by(name='Burgers').first()
            pizza_cat = Category.query.filter_by(name='Pizza').first()
            
            menu_items = [
                MenuItem(name='Classic Burger', price=8.99, category_id=burger_cat.id, description='Juicy beef patty with lettuce, tomato, and cheese'),
                MenuItem(name='Cheese Burger', price=9.99, category_id=burger_cat.id, description='Double cheese with beef patty'),
                MenuItem(name='Margherita Pizza', price=12.99, category_id=pizza_cat.id, description='Fresh tomatoes, mozzarella, and basil'),
                MenuItem(name='Pepperoni Pizza', price=14.99, category_id=pizza_cat.id, description='Classic pepperoni with cheese'),
            ]
            
            for item in menu_items:
                db.session.add(item)
            
            # Add sample offers
            offers = [
                Offer(title='50% Off First Order', description='Get 50% off on your first order', discount_percentage=50.0),
                Offer(title='Buy 2 Get 1 Free', description='Buy 2 pizzas and get 1 free', discount_percentage=33.0),
            ]
            
            for offer in offers:
                db.session.add(offer)
            
            db.session.commit()

if __name__ == '__main__':
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)