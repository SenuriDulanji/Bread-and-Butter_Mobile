"""
Create sample data for testing the recommendation system
"""

import requests
import json
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5002"

def create_sample_categories():
    """Create sample food categories"""
    categories = [
        {"name": "Burgers", "image": "burger.jpg"},
        {"name": "Pizza", "image": "pizza.jpg"}, 
        {"name": "Beverages", "image": "beverage.jpg"},
        {"name": "Desserts", "image": "dessert.jpg"},
        {"name": "Sides", "image": "sides.jpg"},
        {"name": "Salads", "image": "salads.jpg"}
    ]
    
    print("Creating categories...")
    for category in categories:
        # We need to create categories via direct database insertion since there's no API endpoint
        # For now, they'll be created when we create menu items
        pass
    return categories

def create_sample_menu_items():
    """Create sample menu items"""
    menu_items = [
        # Burgers (category_id: 1)
        {"name": "Classic Beef Burger", "price": 12.99, "description": "Juicy beef patty with lettuce, tomato, and cheese", "category_id": 1},
        {"name": "Chicken Deluxe", "price": 11.99, "description": "Grilled chicken breast with avocado and bacon", "category_id": 1},
        {"name": "Veggie Burger", "price": 10.99, "description": "Plant-based patty with fresh vegetables", "category_id": 1},
        {"name": "BBQ Bacon Burger", "price": 14.99, "description": "Beef patty with BBQ sauce, bacon, and onion rings", "category_id": 1},
        
        # Pizza (category_id: 2)
        {"name": "Margherita Pizza", "price": 15.99, "description": "Fresh tomatoes, mozzarella, and basil", "category_id": 2},
        {"name": "Pepperoni Pizza", "price": 17.99, "description": "Classic pepperoni with cheese", "category_id": 2},
        {"name": "Supreme Pizza", "price": 19.99, "description": "Loaded with pepperoni, sausage, vegetables", "category_id": 2},
        {"name": "Hawaiian Pizza", "price": 16.99, "description": "Ham and pineapple with cheese", "category_id": 2},
        
        # Beverages (category_id: 3)
        {"name": "Coca Cola", "price": 2.99, "description": "Classic Coca Cola", "category_id": 3},
        {"name": "Fresh Orange Juice", "price": 4.99, "description": "Fresh squeezed orange juice", "category_id": 3},
        {"name": "Iced Coffee", "price": 3.99, "description": "Cold brew coffee with ice", "category_id": 3},
        {"name": "Milkshake", "price": 5.99, "description": "Vanilla milkshake with whipped cream", "category_id": 3},
        
        # Desserts (category_id: 4)
        {"name": "Chocolate Cake", "price": 6.99, "description": "Rich chocolate cake with frosting", "category_id": 4},
        {"name": "Ice Cream Sundae", "price": 5.99, "description": "Vanilla ice cream with toppings", "category_id": 4},
        {"name": "Apple Pie", "price": 4.99, "description": "Classic apple pie slice", "category_id": 4},
        
        # Sides (category_id: 5)
        {"name": "French Fries", "price": 4.99, "description": "Crispy golden fries", "category_id": 5},
        {"name": "Onion Rings", "price": 5.99, "description": "Crispy breaded onion rings", "category_id": 5},
        {"name": "Garlic Bread", "price": 3.99, "description": "Toasted garlic bread", "category_id": 5},
        
        # Salads (category_id: 6)
        {"name": "Caesar Salad", "price": 8.99, "description": "Crisp romaine with Caesar dressing", "category_id": 6},
        {"name": "Garden Salad", "price": 7.99, "description": "Fresh mixed greens and vegetables", "category_id": 6}
    ]
    
    print("Creating menu items...")
    created_items = []
    
    for item in menu_items:
        try:
            # Create menu item via API (this will also create categories automatically)
            data = {
                'name': item['name'],
                'description': item['description'],
                'price': item['price'],
                'category_id': item['category_id'],
                'is_available': 'true',
                'discount_percentage': random.choice([0, 0, 0, 5, 10, 15])  # Most items no discount
            }
            
            response = requests.post(f"{BASE_URL}/api/menu-items", data=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    created_items.append(result['item'])
                    print(f"Created: {item['name']}")
                else:
                    print(f"Failed to create {item['name']}: {result.get('message', 'Unknown error')}")
            else:
                print(f"Failed to create {item['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Error creating {item['name']}: {str(e)}")
    
    return created_items

def register_sample_users():
    """Register sample users"""
    users = [
        {"username": "alice", "email": "alice@example.com", "phone": "555-0001", "name": "Alice Johnson"},
        {"username": "bob", "email": "bob@example.com", "phone": "555-0002", "name": "Bob Smith"},
        {"username": "charlie", "email": "charlie@example.com", "phone": "555-0003", "name": "Charlie Brown"},
        {"username": "diana", "email": "diana@example.com", "phone": "555-0004", "name": "Diana Wilson"},
        {"username": "eve", "email": "eve@example.com", "phone": "555-0005", "name": "Eve Davis"}
    ]
    
    print("Creating users...")
    created_users = []
    
    for user in users:
        try:
            data = {
                'username': user['username'],
                'email': user['email'],
                'phone': user['phone'],
                'name': user['name'],
                'password': 'password123'  # Simple password for testing
            }
            
            response = requests.post(f"{BASE_URL}/api/register", json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    created_users.append({**user, 'id': result.get('user_id')})
                    print(f"Created user: {user['name']}")
                else:
                    print(f"Failed to create user {user['name']}: {result.get('message', 'Unknown error')}")
            else:
                print(f"Failed to create user {user['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Error creating user {user['name']}: {str(e)}")
    
    return created_users

def create_sample_orders(users, menu_items):
    """Create sample orders for users based on different preferences"""
    print("Creating sample orders...")
    
    # User preferences simulation
    user_preferences = {
        1: {"categories": [1, 5], "price_range": "medium"},  # Alice likes burgers and sides
        2: {"categories": [2, 3], "price_range": "high"},    # Bob likes pizza and beverages  
        3: {"categories": [1, 3, 4], "price_range": "low"},  # Charlie likes burgers, beverages, desserts
        4: {"categories": [6, 4], "price_range": "medium"},  # Diana likes salads and desserts
        5: {"categories": [2, 5, 3], "price_range": "high"}  # Eve likes pizza, sides, beverages
    }
    
    created_orders = []
    
    for user in users:
        if not user.get('id'):
            continue
            
        user_id = user['id']
        preferences = user_preferences.get(user_id, {"categories": [1, 2, 3], "price_range": "medium"})
        
        # Login user to get token
        try:
            login_response = requests.post(f"{BASE_URL}/api/login", json={
                'username': user['username'],
                'password': 'password123'
            })
            
            if login_response.status_code != 200:
                print(f"Failed to login user {user['username']}")
                continue
                
            login_result = login_response.json()
            if not login_result.get('success'):
                print(f"Failed to login user {user['username']}: {login_result.get('message')}")
                continue
                
            token = login_result['access_token']
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            
            # Create 3-8 orders for each user
            num_orders = random.randint(3, 8)
            
            for order_num in range(num_orders):
                # Select items based on user preferences
                preferred_items = [
                    item for item in menu_items 
                    if item.get('category_id') in preferences['categories']
                ]
                
                if not preferred_items:
                    preferred_items = menu_items
                
                # Select 1-4 items for the order
                order_items = []
                num_items = random.randint(1, 4)
                selected_items = random.sample(preferred_items, min(num_items, len(preferred_items)))
                
                total_amount = 0
                for item in selected_items:
                    quantity = random.randint(1, 3)
                    price = item.get('discounted_price', item.get('price', 0))
                    
                    order_items.append({
                        'item_id': item['id'],
                        'name': item['name'],
                        'quantity': quantity,
                        'price': price
                    })
                    
                    total_amount += price * quantity
                
                # Create order
                order_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                order_data = {
                    'items': order_items,
                    'total_amount': total_amount,
                    'delivery_address': f"{random.randint(100, 999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St'])}, {random.choice(['Downtown', 'Uptown', 'Eastside', 'Westside'])}",
                    'phone': user['phone']
                }
                
                response = requests.post(f"{BASE_URL}/api/add_order", json=order_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        created_orders.append(result)
                        print(f"Created order for {user['name']}: ${total_amount:.2f}")
                    else:
                        print(f"Failed to create order for {user['name']}: {result.get('message')}")
                else:
                    print(f"Failed to create order for {user['name']}: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"Error creating orders for {user['name']}: {str(e)}")
    
    return created_orders

def main():
    """Create all sample data"""
    print("Creating sample data for recommendation system testing...")
    
    # Step 1: Create categories (handled automatically by menu items)
    categories = create_sample_categories()
    
    # Step 2: Create menu items
    menu_items = create_sample_menu_items()
    print(f"Created {len(menu_items)} menu items")
    
    # Step 3: Create users
    users = register_sample_users()
    print(f"Created {len(users)} users")
    
    # Step 4: Create orders
    orders = create_sample_orders(users, menu_items)
    print(f"Created {len(orders)} orders")
    
    print("\nSample data creation complete!")
    print("You can now test the recommendation system with:")
    print("- GET /api/recommendations (with JWT token)")
    print("- GET /api/recommendations/{user_id}")

if __name__ == "__main__":
    main()