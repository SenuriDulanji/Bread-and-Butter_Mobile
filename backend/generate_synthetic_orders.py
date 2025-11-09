#!/usr/bin/env python3
"""
Generate synthetic orders from 2025-04-01 to 2025-09-13
Using existing users and menu items only
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
import sys

def get_existing_data():
    """Get existing users and menu items from database"""
    conn = sqlite3.connect('instance/breadandbutter.db')
    cursor = conn.cursor()
    
    # Get users
    cursor.execute("SELECT id, name, phone FROM user")
    users = cursor.fetchall()
    
    # Get menu items
    cursor.execute("SELECT id, name, price, category_id FROM menu_item")
    menu_items = cursor.fetchall()
    
    conn.close()
    
    return users, menu_items

def generate_synthetic_orders(users, menu_items):
    """Generate synthetic orders from 2025-04-01 to 2025-09-13"""
    
    # Date range
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 9, 13)
    
    # User preferences (based on user IDs)
    user_preferences = {
        1: {"favorites": [1, 3, 4], "avg_items": 2, "frequency": 0.3},  # Alice - moderate orders
        2: {"favorites": [2, 5, 6], "avg_items": 3, "frequency": 0.4},  # Bob - frequent orders
        3: {"favorites": [3, 4, 5], "avg_items": 2, "frequency": 0.2},  # Charlie - occasional orders
        4: {"favorites": [1, 6], "avg_items": 1, "frequency": 0.25},    # Diana - light orders
        5: {"favorites": [2, 3, 6], "avg_items": 3, "frequency": 0.35}, # Eve - regular orders
        6: {"favorites": [1, 2, 3, 4, 5, 6], "avg_items": 2, "frequency": 0.3} # ayeshmadusanka - varied
    }
    
    orders = []
    current_date = start_date
    
    print(f"Generating synthetic orders from {start_date.date()} to {end_date.date()}")
    
    while current_date <= end_date:
        # For each day, decide if each user places an order
        for user in users:
            user_id = user[0]
            user_name = user[1]
            user_phone = user[2]
            
            preferences = user_preferences.get(user_id, {"favorites": [1, 2, 3], "avg_items": 2, "frequency": 0.25})
            
            # Random chance of ordering based on user frequency
            if random.random() < preferences["frequency"]:
                # Generate order
                num_items = max(1, int(random.gauss(preferences["avg_items"], 0.5)))
                
                # Select items based on preferences
                available_items = [item for item in menu_items if item[0] in preferences["favorites"]]
                if not available_items:
                    available_items = menu_items
                
                selected_items = random.sample(available_items, min(num_items, len(available_items)))
                
                # Build order items
                order_items = []
                total_amount = 0.0
                
                for item in selected_items:
                    item_id = item[0]
                    item_name = item[1]
                    item_price = item[2]
                    quantity = random.randint(1, 3)
                    
                    order_items.append({
                        'item_id': item_id,
                        'name': item_name,
                        'price': item_price,
                        'quantity': quantity,
                        'total': item_price * quantity
                    })
                    
                    total_amount += item_price * quantity
                
                # Generate random time within the day (business hours 10 AM - 9 PM)
                hour = random.randint(10, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                microsecond = random.randint(0, 999999)
                
                order_time = current_date.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
                
                # Random addresses
                addresses = [
                    "123 Main St, Downtown",
                    "456 Oak Ave, Uptown",
                    "789 Pine Rd, Eastside",
                    "321 Elm St, Westside",
                    "654 Cedar Blvd, Midtown",
                    "987 Maple Dr, Southside"
                ]
                
                order = {
                    'user_id': user_id,
                    'total_amount': round(total_amount, 2),
                    'status': random.choice(['pending', 'completed', 'completed', 'completed']),  # Most completed
                    'delivery_address': random.choice(addresses),
                    'phone': user_phone,
                    'items': json.dumps(order_items),
                    'created_at': order_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                }
                
                orders.append(order)
        
        current_date += timedelta(days=1)
    
    return orders

def insert_orders_to_database(orders):
    """Insert generated orders into the database"""
    conn = sqlite3.connect('instance/breadandbutter.db')
    cursor = conn.cursor()
    
    print(f"Inserting {len(orders)} synthetic orders into database...")
    
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
    print("=== Synthetic Order Generator ===")
    
    # Get existing data
    users, menu_items = get_existing_data()
    
    print(f"Found {len(users)} users and {len(menu_items)} menu items")
    
    # Generate synthetic orders
    orders = generate_synthetic_orders(users, menu_items)
    
    print(f"Generated {len(orders)} synthetic orders")
    
    # Show some statistics
    user_order_counts = {}
    for order in orders:
        user_id = order['user_id']
        user_order_counts[user_id] = user_order_counts.get(user_id, 0) + 1
    
    print("\nOrder distribution by user:")
    for user in users:
        user_id = user[0]
        user_name = user[1]
        count = user_order_counts.get(user_id, 0)
        print(f"  {user_name}: {count} orders")
    
    # Auto-confirm insertion
    print(f"\nInserting {len(orders)} orders into the database...")
    insert_orders_to_database(orders)
    print("Synthetic orders generated successfully!")

if __name__ == "__main__":
    main()