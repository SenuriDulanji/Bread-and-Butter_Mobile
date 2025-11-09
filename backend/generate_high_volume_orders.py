#!/usr/bin/env python3
"""
Generate high volume synthetic orders from 2025-04-01 to 2025-04-13 (target 100+ orders)
Using existing users and menu items only
Order statuses: pending, confirmed, preparing, ready, delivered
"""

import sqlite3
import json
import random
import math
from datetime import datetime, timedelta
import numpy as np

def get_existing_data():
    """Get existing users and menu items from database"""
    conn = sqlite3.connect('instance/breadandbutter.db')
    cursor = conn.cursor()
    
    # Clear existing orders first
    cursor.execute("DELETE FROM \"order\"")
    
    # Get users
    cursor.execute("SELECT id, name, phone FROM user")
    users = cursor.fetchall()
    
    # Get menu items
    cursor.execute("SELECT id, name, price, category_id FROM menu_item")
    menu_items = cursor.fetchall()
    
    conn.commit()
    conn.close()
    
    return users, menu_items

def calculate_base_demand(date):
    """Calculate base demand - much higher volume (15-25 orders per day)"""
    return random.randint(15, 25)

def calculate_weekly_multiplier(date):
    """Calculate weekly pattern multiplier"""
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    
    # Weekend is busier for food delivery
    weekly_multipliers = {
        0: 0.8,   # Monday
        1: 0.9,   # Tuesday
        2: 0.95,  # Wednesday
        3: 1.0,   # Thursday
        4: 1.3,   # Friday
        5: 1.5,   # Saturday
        6: 1.4,   # Sunday
    }
    
    return weekly_multipliers[weekday]

def calculate_daily_pattern(hour):
    """Calculate hourly demand pattern"""
    # Lunch peak (11 AM - 2 PM) and dinner peak (6 PM - 9 PM)
    if 11 <= hour <= 14:  # Lunch peak
        return 1.5 + 0.3 * math.sin(math.pi * (hour - 11) / 3)
    elif 18 <= hour <= 21:  # Dinner peak
        return 1.8 + 0.4 * math.sin(math.pi * (hour - 18) / 3)
    elif 15 <= hour <= 17:  # Afternoon lull
        return 0.4
    elif 22 <= hour <= 23 or 10 <= hour <= 10:  # Late night/early morning
        return 0.6
    else:  # Night/very early morning
        return 0.2

def get_user_behavior_patterns():
    """Define realistic user behavior patterns"""
    return {
        1: {  # Alice - regular office worker
            "weekday_preference": 1.2,
            "lunch_preference": 1.5,
            "favorite_items": [1, 3, 4],  # Pizza, burger, milkshake
            "avg_order_size": 2.0,
            "price_sensitivity": 0.8,
            "order_frequency": 0.4,  # Higher frequency
        },
        2: {  # Bob - weekend social eater
            "weekend_preference": 1.8,
            "dinner_preference": 1.6,
            "favorite_items": [2, 5, 6],  # Chilli pizza, strawberry shake, lava cake
            "avg_order_size": 3.0,
            "price_sensitivity": 0.5,
            "order_frequency": 0.5,
        },
        3: {  # Charlie - student with tight budget
            "weekday_preference": 0.8,
            "lunch_preference": 1.8,
            "favorite_items": [3, 4, 5],  # Cheap options
            "avg_order_size": 1.5,
            "price_sensitivity": 1.5,
            "order_frequency": 0.6,  # Orders frequently but small amounts
        },
        4: {  # Diana - health-conscious
            "weekday_preference": 1.1,
            "lunch_preference": 1.3,
            "favorite_items": [1, 4],   # Veggie pizza, mango shake
            "avg_order_size": 1.8,
            "price_sensitivity": 0.7,
            "order_frequency": 0.3,
        },
        5: {  # Eve - busy professional
            "weekday_preference": 1.4,
            "dinner_preference": 1.7,
            "favorite_items": [2, 3, 6],  # Premium items
            "avg_order_size": 2.5,
            "price_sensitivity": 0.4,
            "order_frequency": 0.5,
        },
        6: {  # ayeshmadusanka - varied pattern
            "weekend_preference": 1.3,
            "balanced_timing": True,
            "favorite_items": [1, 2, 3, 4, 5, 6],  # All items
            "avg_order_size": 2.2,
            "price_sensitivity": 0.6,
            "order_frequency": 0.4,
        }
    }

def get_order_status_based_on_age(days_ago):
    """Get realistic order status based on how old the order is"""
    if days_ago == 0:  # Today (April 13)
        return random.choices(['pending', 'confirmed', 'preparing', 'ready'], weights=[0.3, 0.3, 0.3, 0.1])[0]
    elif days_ago == 1:  # Yesterday (April 12)
        return random.choices(['confirmed', 'preparing', 'ready', 'delivered'], weights=[0.1, 0.2, 0.3, 0.4])[0]
    elif days_ago == 2:  # April 11
        return random.choices(['preparing', 'ready', 'delivered'], weights=[0.1, 0.2, 0.7])[0]
    elif days_ago <= 5:  # April 8-10
        return random.choices(['ready', 'delivered'], weights=[0.1, 0.9])[0]
    else:  # Older orders (April 1-7)
        return 'delivered'

def generate_high_volume_orders(users, menu_items):
    """Generate high volume orders from April 1-13, 2025"""
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 4, 13)
    current_time = datetime(2025, 4, 13, 23, 59, 59)  # Current time for status calculation
    
    user_patterns = get_user_behavior_patterns()
    
    orders = []
    current_date = start_date
    
    print(f"Generating high volume orders from {start_date.date()} to {end_date.date()}")
    print("Target: 100+ orders with multiple orders per day")
    print("Patterns included:")
    print("- Weekly cycles (weekend peaks)")
    print("- Daily patterns (lunch & dinner peaks)")
    print("- Individual user behavior patterns")
    print("- All order statuses: pending, confirmed, preparing, ready, delivered")
    
    total_orders_generated = 0
    
    while current_date <= end_date:
        # Calculate demand for the day
        base_demand = calculate_base_demand(current_date)
        weekly_mult = calculate_weekly_multiplier(current_date)
        
        # Calculate total daily demand (much higher)
        daily_demand = base_demand * weekly_mult
        target_daily_orders = int(daily_demand)
        
        # Generate orders throughout the day
        daily_orders = 0
        attempts = 0
        max_attempts = target_daily_orders * 3  # Allow more attempts to reach target
        
        # Distribute orders across business hours
        business_hours = list(range(10, 23))  # 10 AM - 11 PM
        
        while daily_orders < target_daily_orders and attempts < max_attempts:
            attempts += 1
            
            # Select random hour with preference for peak times
            if random.random() < 0.6:  # 60% chance for peak hours
                if random.random() < 0.5:
                    hour = random.choice([11, 12, 13, 14])  # Lunch peak
                else:
                    hour = random.choice([18, 19, 20, 21])  # Dinner peak
            else:
                hour = random.choice(business_hours)
            
            # Select user based on their behavior pattern
            user = random.choice(users)
            user_id = user[0]
            user_name = user[1]
            user_phone = user[2]
            
            user_pattern = user_patterns.get(user_id, user_patterns[1])
            
            # Check if user should order based on their patterns
            user_prob = user_pattern.get("order_frequency", 0.3)
            
            # Apply user preferences
            if current_date.weekday() >= 5:  # Weekend
                user_prob *= user_pattern.get("weekend_preference", 1.0)
            else:  # Weekday
                user_prob *= user_pattern.get("weekday_preference", 1.0)
            
            # Apply time preferences
            if 11 <= hour <= 14:  # Lunch time
                user_prob *= user_pattern.get("lunch_preference", 1.0)
            elif 18 <= hour <= 21:  # Dinner time
                user_prob *= user_pattern.get("dinner_preference", 1.0)
            
            # Skip if user won't order
            if random.random() > user_prob:
                continue
            
            # Generate order items based on user preferences
            favorite_items = [item for item in menu_items if item[0] in user_pattern["favorite_items"]]
            if not favorite_items:
                favorite_items = menu_items
            
            # Determine order size
            avg_size = user_pattern["avg_order_size"]
            order_size = max(1, int(np.random.poisson(avg_size)))
            order_size = min(order_size, len(favorite_items))
            
            selected_items = random.sample(favorite_items, order_size)
            
            # Build order
            order_items = []
            total_amount = 0.0
            
            for item in selected_items:
                item_id = item[0]
                item_name = item[1]
                item_price = item[2]
                
                # Quantity based on price sensitivity
                if user_pattern["price_sensitivity"] > 1.0 and item_price > 5.0:
                    quantity = 1  # Price sensitive users order less of expensive items
                elif user_pattern["price_sensitivity"] < 0.5:
                    quantity = random.randint(1, 3)  # Price insensitive users order more
                else:
                    quantity = random.randint(1, 2)
                
                order_items.append({
                    'item_id': item_id,
                    'name': item_name,
                    'price': item_price,
                    'quantity': quantity,
                    'total': item_price * quantity
                })
                
                total_amount += item_price * quantity
            
            # Generate realistic timestamp
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            microsecond = random.randint(0, 999999)
            
            order_time = current_date.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
            
            # Calculate order status based on age
            days_ago = (current_time.date() - order_time.date()).days
            status = get_order_status_based_on_age(days_ago)
            
            # Realistic addresses
            addresses = [
                "123 Main St, Downtown",
                "456 Oak Ave, Uptown", 
                "789 Pine Rd, Eastside",
                "321 Elm St, Westside",
                "654 Cedar Blvd, Midtown",
                "987 Maple Dr, Southside",
                "147 University Ave, Campus",
                "258 Business Park Dr, Corporate",
                "369 Residential Ln, Suburbs",
                "159 Food Court Plaza, Mall",
                "741 Industrial Way, Factory District",
                "852 Parkview Terrace, Hillside",
                "963 Riverside Dr, Waterfront"
            ]
            
            order = {
                'user_id': user_id,
                'total_amount': round(total_amount, 2),
                'status': status,
                'delivery_address': random.choice(addresses),
                'phone': user_phone,
                'items': json.dumps(order_items),
                'created_at': order_time.strftime('%Y-%m-%d %H:%M:%S.%f')
            }
            
            orders.append(order)
            daily_orders += 1
            total_orders_generated += 1
        
        print(f"  {current_date.date()} ({current_date.strftime('%A')}): {daily_orders} orders (target: {target_daily_orders})")
        
        current_date += timedelta(days=1)
    
    print(f"\nGenerated {total_orders_generated} orders with realistic patterns")
    return orders

def analyze_patterns(orders):
    """Analyze the generated patterns"""
    print("\n=== Pattern Analysis ===")
    
    # Status distribution
    status_counts = {}
    for order in orders:
        status = order['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\nTotal Orders: {len(orders)}")
    print("\nOrder Status Distribution:")
    for status in ['pending', 'confirmed', 'preparing', 'ready', 'delivered']:
        count = status_counts.get(status, 0)
        percentage = (count / len(orders)) * 100
        print(f"  {status}: {count} orders ({percentage:.1f}%)")
    
    # Daily pattern analysis
    daily_counts = {}
    for order in orders:
        date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        day = date.strftime('%Y-%m-%d (%A)')
        daily_counts[day] = daily_counts.get(day, 0) + 1
    
    print("\nDaily Pattern:")
    for day in sorted(daily_counts.keys()):
        print(f"  {day}: {daily_counts[day]} orders")
    
    # Average orders per day
    avg_orders = len(orders) / 13  # 13 days
    print(f"\nAverage orders per day: {avg_orders:.1f}")

def insert_orders_to_database(orders):
    """Insert generated orders into the database"""
    conn = sqlite3.connect('instance/breadandbutter.db')
    cursor = conn.cursor()
    
    print(f"\nInserting {len(orders)} orders into database...")
    
    for order in orders:
        cursor.execute("""
            INSERT INTO "order" (user_id, total_amount, status, delivery_address, phone, items, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order['user_id'],
            order['total_amount'],
            order['status'],
            order['delivery_address'],
            order['phone'],
            order['items'],
            order['created_at']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Successfully inserted {len(orders)} orders")

def main():
    print("=== High Volume Order Generator ===")
    
    # Get existing data and clear previous orders
    users, menu_items = get_existing_data()
    
    print(f"Found {len(users)} users and {len(menu_items)} menu items")
    print("Cleared existing orders from database")
    
    # Generate high volume orders
    orders = generate_high_volume_orders(users, menu_items)
    
    # Analyze patterns
    analyze_patterns(orders)
    
    # Insert into database
    insert_orders_to_database(orders)
    
    print(f"\n✅ Generated {len(orders)} orders from April 1-13, 2025!")
    print("Order statuses: pending, confirmed, preparing, ready, delivered")
    print("Multiple orders per day with realistic business patterns")
    print("Ready for admin panel and mobile app!")

if __name__ == "__main__":
    main()