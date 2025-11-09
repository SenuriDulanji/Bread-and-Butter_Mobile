#!/usr/bin/env python3
"""
Generate synthetic orders with realistic business patterns for forecasting
Includes:
- Weekly cycles (higher on weekends)
- Daily patterns (lunch and dinner peaks)
- Seasonal trends (summer growth)
- Monthly growth trend
- Special event spikes
- Weather impact simulation
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
    
    # Clear existing orders to start fresh
    cursor.execute("DELETE FROM \"order\" WHERE created_at >= '2025-04-01'")
    
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
    """Calculate base demand with seasonal and growth trends"""
    # Days since start (April 1, 2025)
    start_date = datetime(2025, 4, 1)
    days_since_start = (date - start_date).days
    
    # Base demand starts at 100 orders/day
    base_demand = 100
    
    # Monthly growth trend (3% per month)
    monthly_growth = 1.03 ** (days_since_start / 30.0)
    
    # Seasonal factor (summer is busier for food delivery)
    month = date.month
    if month in [6, 7, 8]:  # Summer peak
        seasonal_factor = 1.4
    elif month in [4, 5, 9]:  # Spring/early fall
        seasonal_factor = 1.2
    elif month in [10, 11]:  # Late fall
        seasonal_factor = 0.9
    else:  # Winter (not in our range, but for completeness)
        seasonal_factor = 0.8
    
    return base_demand * monthly_growth * seasonal_factor

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

def get_special_events():
    """Define special events that cause demand spikes"""
    return [
        # Format: (date, multiplier, description)
        (datetime(2025, 4, 15), 2.0, "Local festival"),
        (datetime(2025, 5, 1), 1.8, "May Day holiday"),
        (datetime(2025, 5, 15), 1.6, "University graduation"),
        (datetime(2025, 6, 1), 1.7, "Start of summer season"),
        (datetime(2025, 6, 21), 2.2, "Summer solstice celebration"),
        (datetime(2025, 7, 4), 2.5, "Independence Day"),
        (datetime(2025, 7, 20), 1.9, "Summer food festival"),
        (datetime(2025, 8, 15), 1.8, "Back to school promotion"),
        (datetime(2025, 9, 1), 1.6, "Labor Day weekend"),
    ]

def simulate_weather_impact(date):
    """Simulate weather impact on orders"""
    # Use date as seed for consistent "weather"
    random.seed(date.toordinal())
    
    # Simulate weather conditions
    weather_chance = random.random()
    
    if weather_chance < 0.1:  # 10% chance of bad weather (increases delivery orders)
        multiplier = 1.4
    elif weather_chance < 0.2:  # 10% chance of very nice weather (decreases orders)
        multiplier = 0.8
    else:  # 80% chance of normal weather
        multiplier = 1.0
    
    # Reset random seed
    random.seed()
    return multiplier

def get_user_behavior_patterns():
    """Define realistic user behavior patterns"""
    return {
        1: {  # Alice - regular office worker
            "weekday_preference": 1.2,  # Orders more on weekdays
            "lunch_preference": 1.5,    # Prefers lunch orders
            "favorite_items": [1, 3, 4],  # Pizza, burger, milkshake
            "avg_order_size": 2.0,
            "price_sensitivity": 0.8,  # Moderate price sensitivity
        },
        2: {  # Bob - weekend social eater
            "weekend_preference": 1.8,  # Much more active on weekends
            "dinner_preference": 1.6,   # Prefers dinner orders
            "favorite_items": [2, 5, 6],  # Chilli pizza, strawberry shake, lava cake
            "avg_order_size": 3.0,
            "price_sensitivity": 0.5,  # Less price sensitive
        },
        3: {  # Charlie - student with tight budget
            "weekday_preference": 0.8,
            "lunch_preference": 1.8,    # Student lunch pattern
            "favorite_items": [3, 4, 5],  # Cheap options
            "avg_order_size": 1.5,
            "price_sensitivity": 1.5,  # Very price sensitive
        },
        4: {  # Diana - health-conscious
            "weekday_preference": 1.1,
            "lunch_preference": 1.3,
            "favorite_items": [1, 4],   # Veggie pizza, mango shake
            "avg_order_size": 1.8,
            "price_sensitivity": 0.7,
        },
        5: {  # Eve - busy professional
            "weekday_preference": 1.4,
            "dinner_preference": 1.7,
            "favorite_items": [2, 3, 6],  # Premium items
            "avg_order_size": 2.5,
            "price_sensitivity": 0.4,  # Low price sensitivity
        },
        6: {  # ayeshmadusanka - varied pattern
            "weekend_preference": 1.3,
            "balanced_timing": True,    # Orders throughout the day
            "favorite_items": [1, 2, 3, 4, 5, 6],  # All items
            "avg_order_size": 2.2,
            "price_sensitivity": 0.6,
        }
    }

def generate_patterned_orders(users, menu_items):
    """Generate orders with realistic patterns"""
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 9, 13)
    
    special_events = get_special_events()
    user_patterns = get_user_behavior_patterns()
    
    orders = []
    current_date = start_date
    
    print(f"Generating patterned orders from {start_date.date()} to {end_date.date()}")
    print("Patterns included:")
    print("- Monthly growth trend (3% per month)")
    print("- Seasonal variations (summer peak)")
    print("- Weekly cycles (weekend peaks)")
    print("- Daily patterns (lunch & dinner peaks)")
    print("- Special events and weather simulation")
    print("- Individual user behavior patterns")
    
    total_orders_generated = 0
    
    while current_date <= end_date:
        # Calculate base demand for the day
        base_demand = calculate_base_demand(current_date)
        weekly_mult = calculate_weekly_multiplier(current_date)
        weather_mult = simulate_weather_impact(current_date)
        
        # Check for special events
        event_mult = 1.0
        for event_date, mult, description in special_events:
            if abs((current_date - event_date).days) <= 1:  # Event lasts 1-2 days
                event_mult = mult
                print(f"  Special event on {current_date.date()}: {description} (x{mult})")
                break
        
        # Calculate total daily demand
        daily_demand = base_demand * weekly_mult * weather_mult * event_mult
        
        # Generate orders throughout the day with hourly patterns
        daily_orders = 0
        for hour in range(10, 23):  # Business hours 10 AM - 11 PM
            hourly_mult = calculate_daily_pattern(hour)
            hourly_demand = daily_demand * hourly_mult / 13  # Distribute across 13 hours
            
            # Convert demand to actual orders with some randomness
            orders_this_hour = max(0, int(np.random.poisson(hourly_demand / 13)))
            
            for _ in range(orders_this_hour):
                # Select user based on their behavior pattern
                user = random.choice(users)
                user_id = user[0]
                user_name = user[1]
                user_phone = user[2]
                
                user_pattern = user_patterns.get(user_id, user_patterns[1])
                
                # Check if user should order based on their patterns
                user_prob = 0.3  # Base probability
                
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
                    base_qty = 1
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
                    "159 Food Court Plaza, Mall"
                ]
                
                # Status based on date (recent orders more likely to be pending)
                days_ago = (datetime(2025, 9, 13) - order_time).days
                if days_ago < 2:
                    status = random.choices(['pending', 'confirmed', 'completed'], weights=[0.3, 0.3, 0.4])[0]
                elif days_ago < 7:
                    status = random.choices(['pending', 'completed'], weights=[0.1, 0.9])[0]
                else:
                    status = 'completed'
                
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
        
        if daily_orders > 0:
            print(f"  {current_date.date()}: {daily_orders} orders (base: {base_demand:.1f}, weekly: {weekly_mult:.1f}x, weather: {weather_mult:.1f}x, event: {event_mult:.1f}x)")
        
        current_date += timedelta(days=1)
    
    print(f"\nGenerated {total_orders_generated} patterned orders with realistic business trends")
    return orders

def analyze_patterns(orders):
    """Analyze the generated patterns"""
    print("\n=== Pattern Analysis ===")
    
    # Weekly pattern analysis
    weekly_counts = [0] * 7
    for order in orders:
        date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        weekly_counts[date.weekday()] += 1
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    print("\nWeekly Pattern:")
    for i, day in enumerate(days):
        print(f"  {day}: {weekly_counts[i]} orders")
    
    # Monthly pattern analysis
    monthly_counts = {}
    for order in orders:
        date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        month = date.strftime('%Y-%m')
        monthly_counts[month] = monthly_counts.get(month, 0) + 1
    
    print("\nMonthly Pattern:")
    for month in sorted(monthly_counts.keys()):
        print(f"  {month}: {monthly_counts[month]} orders")
    
    # Hourly pattern analysis
    hourly_counts = [0] * 24
    for order in orders:
        date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        hourly_counts[date.hour] += 1
    
    print("\nPeak Hours:")
    for hour in range(24):
        if hourly_counts[hour] > 0:
            print(f"  {hour:02d}:00 - {hourly_counts[hour]} orders")

def insert_orders_to_database(orders):
    """Insert generated orders into the database"""
    conn = sqlite3.connect('instance/breadandbutter.db')
    cursor = conn.cursor()
    
    print(f"\nInserting {len(orders)} patterned orders into database...")
    
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
    
    print(f"Successfully inserted {len(orders)} patterned orders")

def main():
    print("=== Patterned Order Generator for Forecasting ===")
    
    # Get existing data and clear previous synthetic orders
    users, menu_items = get_existing_data()
    
    print(f"Found {len(users)} users and {len(menu_items)} menu items")
    print("Cleared existing synthetic orders from database")
    
    # Generate patterned orders
    orders = generate_patterned_orders(users, menu_items)
    
    # Analyze patterns
    analyze_patterns(orders)
    
    # Insert into database
    insert_orders_to_database(orders)
    
    print(f"\n✅ Generated {len(orders)} orders with realistic patterns for forecasting!")
    print("These orders include:")
    print("  📈 Growth trends")  
    print("  📅 Seasonal variations")
    print("  📊 Weekly cycles")
    print("  🕐 Daily patterns")
    print("  🎉 Special events")
    print("  🌤️  Weather impact")
    print("  👤 User behavior patterns")

if __name__ == "__main__":
    main()