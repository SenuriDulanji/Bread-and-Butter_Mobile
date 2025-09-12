#!/usr/bin/env python3
import os
import sys
sys.path.append('/Users/mac/AndroidStudioProjects/breadandbutter/backend')

from app import app, db, User, Order, MenuItem, Category
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

def create_sample_users_if_needed():
    """Create sample users for synthetic orders"""
    if User.query.count() < 10:
        sample_users = [
            {'phone': '0712345678', 'name': 'John Doe', 'email': 'john@example.com'},
            {'phone': '0723456789', 'name': 'Jane Smith', 'email': 'jane@example.com'},
            {'phone': '0734567890', 'name': 'Mike Johnson', 'email': 'mike@example.com'},
            {'phone': '0745678901', 'name': 'Sarah Wilson', 'email': 'sarah@example.com'},
            {'phone': '0756789012', 'name': 'David Brown', 'email': 'david@example.com'},
            {'phone': '0767890123', 'name': 'Lisa Davis', 'email': 'lisa@example.com'},
            {'phone': '0778901234', 'name': 'Tom Miller', 'email': 'tom@example.com'},
            {'phone': '0789012345', 'name': 'Emma Garcia', 'email': 'emma@example.com'},
            {'phone': '0790123456', 'name': 'James Wilson', 'email': 'james@example.com'},
            {'phone': '0701234567', 'name': 'Olivia Taylor', 'email': 'olivia@example.com'},
        ]
        
        import bcrypt
        for user_data in sample_users:
            if not User.query.filter_by(phone=user_data['phone']).first():
                hashed_password = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
                user = User(
                    phone=user_data['phone'],
                    name=user_data['name'],
                    email=user_data['email'],
                    password=hashed_password,
                    is_verified=True,
                    loyalty_points=random.randint(0, 500)
                )
                db.session.add(user)
        
        db.session.commit()
        print(f"Created {len(sample_users)} sample users")

def create_sample_menu_items_if_needed():
    """Create comprehensive menu items for realistic orders"""
    if MenuItem.query.count() < 20:
        # Ensure categories exist
        categories = ['Burgers', 'Pizza', 'Beverages', 'Desserts', 'Sides', 'Salads']
        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name, image=f'{cat_name.lower()}.jpg')
                db.session.add(category)
        
        db.session.commit()
        
        # Create menu items
        menu_data = [
            # Burgers
            {'name': 'Classic Burger', 'price': 8.99, 'category': 'Burgers', 'description': 'Juicy beef patty with lettuce, tomato, and cheese'},
            {'name': 'Cheese Burger', 'price': 9.99, 'category': 'Burgers', 'description': 'Double cheese with beef patty'},
            {'name': 'BBQ Burger', 'price': 11.99, 'category': 'Burgers', 'description': 'BBQ sauce, bacon, and onion rings'},
            {'name': 'Veggie Burger', 'price': 9.49, 'category': 'Burgers', 'description': 'Plant-based patty with fresh vegetables'},
            
            # Pizza
            {'name': 'Margherita Pizza', 'price': 12.99, 'category': 'Pizza', 'description': 'Fresh tomatoes, mozzarella, and basil'},
            {'name': 'Pepperoni Pizza', 'price': 14.99, 'category': 'Pizza', 'description': 'Classic pepperoni with cheese'},
            {'name': 'Supreme Pizza', 'price': 17.99, 'category': 'Pizza', 'description': 'Loaded with pepperoni, sausage, vegetables'},
            {'name': 'Hawaiian Pizza', 'price': 15.99, 'category': 'Pizza', 'description': 'Ham and pineapple with cheese'},
            
            # Beverages
            {'name': 'Coca Cola', 'price': 2.49, 'category': 'Beverages', 'description': 'Classic Coca Cola'},
            {'name': 'Orange Juice', 'price': 3.99, 'category': 'Beverages', 'description': 'Fresh squeezed orange juice'},
            {'name': 'Coffee', 'price': 2.99, 'category': 'Beverages', 'description': 'Freshly brewed coffee'},
            {'name': 'Iced Tea', 'price': 2.79, 'category': 'Beverages', 'description': 'Refreshing iced tea'},
            
            # Desserts
            {'name': 'Chocolate Cake', 'price': 5.99, 'category': 'Desserts', 'description': 'Rich chocolate cake with frosting'},
            {'name': 'Ice Cream', 'price': 3.99, 'category': 'Desserts', 'description': 'Vanilla ice cream scoop'},
            {'name': 'Apple Pie', 'price': 4.99, 'category': 'Desserts', 'description': 'Classic apple pie slice'},
            
            # Sides
            {'name': 'French Fries', 'price': 3.49, 'category': 'Sides', 'description': 'Crispy golden fries'},
            {'name': 'Onion Rings', 'price': 4.49, 'category': 'Sides', 'description': 'Crispy breaded onion rings'},
            {'name': 'Garlic Bread', 'price': 3.99, 'category': 'Sides', 'description': 'Toasted garlic bread'},
            
            # Salads
            {'name': 'Caesar Salad', 'price': 7.99, 'category': 'Salads', 'description': 'Crisp romaine with Caesar dressing'},
            {'name': 'Garden Salad', 'price': 6.99, 'category': 'Salads', 'description': 'Fresh mixed greens and vegetables'},
        ]
        
        for item_data in menu_data:
            category = Category.query.filter_by(name=item_data['category']).first()
            if category and not MenuItem.query.filter_by(name=item_data['name']).first():
                item = MenuItem(
                    name=item_data['name'],
                    price=item_data['price'],
                    category_id=category.id,
                    description=item_data['description'],
                    is_available=True,
                    discount_percentage=random.choice([0, 0, 0, 5, 10, 15]) if random.random() < 0.3 else 0
                )
                db.session.add(item)
        
        db.session.commit()
        print(f"Created {len(menu_data)} menu items")

def generate_synthetic_orders():
    """Generate realistic synthetic orders based on our forecast data"""
    
    # Read our forecast data for realistic order counts
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 9, 12)
    
    # Get all users and menu items
    users = User.query.all()
    menu_items = MenuItem.query.all()
    
    if not users or not menu_items:
        print("Error: Need users and menu items to generate orders")
        return
    
    np.random.seed(42)  # For reproducible results
    
    orders_created = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Calculate base order count (similar to our forecast)
        days_since_start = (current_date - start_date).days
        base_orders = 50 + (days_since_start * 0.3)  # Growing trend
        
        # Weekly seasonality (higher on weekends)
        weekday = current_date.weekday()
        if weekday in [5, 6]:  # Saturday, Sunday
            weekend_multiplier = 1.4
        elif weekday in [4]:  # Friday
            weekend_multiplier = 1.2
        else:
            weekend_multiplier = 1.0
        
        # Monthly seasonality
        day_of_month = current_date.day
        if day_of_month <= 5 or day_of_month >= 25:
            monthly_multiplier = 1.1
        else:
            monthly_multiplier = 1.0
        
        # Holiday effects
        holiday_multiplier = 1.0
        if current_date.month == 2 and current_date.day == 14:  # Valentine's Day
            holiday_multiplier = 1.8
        elif current_date.month == 3 and current_date.day in range(15, 22):  # Spring break
            holiday_multiplier = 1.3
        elif current_date.month == 7 and current_date.day == 4:  # Independence Day
            holiday_multiplier = 1.6
        elif current_date.month == 8 and current_date.day in range(1, 15):  # Summer vacation
            holiday_multiplier = 1.2
        
        # Random noise
        noise = np.random.normal(0, 8)
        
        # Calculate final order count for this day
        daily_orders = max(5, int(base_orders * weekend_multiplier * monthly_multiplier * holiday_multiplier + noise))
        
        # Generate orders for this day
        for _ in range(daily_orders):
            # Random time during the day (with business hour preferences)
            if current_date.weekday() < 5:  # Weekday
                # Peak hours: 12-1pm and 6-8pm
                hour_weights = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.8, 1.0, 1.2, 2.5, 3.0, 2.0, 1.0, 0.8, 0.8, 1.2, 2.8, 3.5, 2.2, 1.5, 1.0, 0.7]
            else:  # Weekend
                # More distributed throughout the day
                hour_weights = [0.3, 0.2, 0.2, 0.2, 0.3, 0.5, 0.8, 1.2, 1.5, 2.0, 2.5, 3.0, 3.2, 2.8, 2.5, 2.0, 1.8, 2.2, 2.8, 3.0, 2.5, 2.0, 1.5, 1.0]
            
            hour = np.random.choice(24, p=np.array(hour_weights)/np.sum(hour_weights))
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            order_time = current_date.replace(hour=hour, minute=minute, second=second)
            
            # Select random user
            user = random.choice(users)
            
            # Generate order items (1-5 items per order)
            num_items = np.random.choice([1, 2, 3, 4, 5], p=[0.3, 0.35, 0.2, 0.1, 0.05])
            order_items = []
            total_amount = 0
            
            selected_items = random.sample(menu_items, min(num_items, len(menu_items)))
            
            for menu_item in selected_items:
                quantity = int(np.random.choice([1, 2, 3], p=[0.7, 0.25, 0.05]))
                item_price = float(menu_item.price)
                
                # Apply discount if available
                if menu_item.discount_percentage > 0:
                    item_price = item_price * (1 - menu_item.discount_percentage / 100)
                
                item_total = item_price * quantity
                total_amount += item_total
                
                order_items.append({
                    'item_id': int(menu_item.id),
                    'name': str(menu_item.name),
                    'price': float(item_price),
                    'quantity': int(quantity),
                    'total': float(item_total)
                })
            
            # Random delivery address
            addresses = [
                "123 Main Street, Downtown",
                "456 Oak Avenue, Riverside",
                "789 Pine Road, Hillview",
                "321 Elm Street, Sunset",
                "654 Maple Drive, Garden District",
                "987 Cedar Lane, Parkview",
                "147 Birch Street, Westside",
                "258 Ash Avenue, Northgate",
                "369 Willow Road, Eastside",
                "741 Palm Street, Southview"
            ]
            
            # Random status based on order age
            days_old = (datetime(2025, 9, 12) - order_time).days
            if days_old > 7:
                status = 'delivered'
            elif days_old > 3:
                status = random.choice(['delivered', 'delivered', 'delivered', 'ready'])
            elif days_old > 1:
                status = random.choice(['delivered', 'ready', 'preparing'])
            else:
                status = random.choice(['pending', 'confirmed', 'preparing'])
            
            # Create order
            order = Order(
                user_id=user.id,
                total_amount=round(total_amount, 2),
                status=status,
                delivery_address=random.choice(addresses),
                phone=user.phone,
                items=json.dumps(order_items),
                created_at=order_time
            )
            
            db.session.add(order)
            orders_created += 1
            
            # Commit in batches for better performance
            if orders_created % 100 == 0:
                db.session.commit()
                print(f"Created {orders_created} orders...")
        
        current_date += timedelta(days=1)
    
    # Final commit
    db.session.commit()
    print(f"Successfully created {orders_created} synthetic orders from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    return orders_created

def main():
    with app.app_context():
        print("Initializing database and sample data...")
        
        # Ensure tables exist
        db.create_all()
        
        # Create sample users and menu items if needed
        create_sample_users_if_needed()
        create_sample_menu_items_if_needed()
        
        # Check if orders already exist
        existing_orders = Order.query.count()
        if existing_orders > 0:
            print(f"Found {existing_orders} existing orders. Deleting and recreating...")
            Order.query.delete()
            db.session.commit()
            print("Deleted existing orders")
        
        # Generate synthetic orders
        print("Generating synthetic orders...")
        orders_created = generate_synthetic_orders()
        
        # Print summary
        total_orders = Order.query.count()
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
        
        print(f"\n📊 ORDER GENERATION SUMMARY:")
        print(f"{'='*50}")
        print(f"Total Orders Created: {orders_created}")
        print(f"Total Orders in DB: {total_orders}")
        print(f"Total Revenue: ${total_revenue:.2f}")
        print(f"Average Order Value: ${total_revenue/total_orders:.2f}")
        print(f"Period: 2025-01-01 to 2025-09-12")
        
        # Status breakdown
        status_counts = {}
        for status in ['pending', 'confirmed', 'preparing', 'ready', 'delivered']:
            count = Order.query.filter_by(status=status).count()
            status_counts[status] = count
            print(f"{status.title()} Orders: {count}")
        
        print(f"{'='*50}")

if __name__ == "__main__":
    main()