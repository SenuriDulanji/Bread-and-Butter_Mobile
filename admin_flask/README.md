# Bread and Butter Admin Panel

A modern Flask-based admin panel for the Bread and Butter restaurant management system, built with Jinja templating and Tailwind CSS.

## Features

- 🔐 **Secure Authentication** - Admin login with password hashing
- 📊 **Dashboard** - Overview statistics and quick actions
- 👥 **User Management** - View and manage registered users
- 🍽️ **Menu Management** - Add, edit, delete menu items with image support
- 📋 **Order Management** - Track and update order statuses
- 🎨 **Modern UI** - Built with Tailwind CSS for a responsive, modern interface
- ⚡ **Real-time Updates** - Dynamic filtering and search functionality

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Template Engine**: Jinja2
- **Frontend**: Tailwind CSS, Font Awesome icons
- **Database**: MySQL
- **Authentication**: Session-based with password hashing

## Installation

### Prerequisites

- Python 3.7+
- MySQL Server
- pip (Python package installer)

### Setup Steps

1. **Clone or navigate to the admin_flask directory**
   ```bash
   cd admin_flask
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file with your database credentials and configuration.

5. **Set up the database**
   - Ensure your MySQL server is running
   - Create the database: `bread_and_butter`
   - Import your existing database schema or create the required tables:
     - `bread_admin` - Admin users
     - `bread_users` - Regular users
     - `bread_items` - Menu items
     - `bread_orders` - Customer orders

6. **Run the application**
   ```bash
   python run.py
   ```
   or
   ```bash
   python app.py
   ```

The admin panel will be available at `http://localhost:5000`

## Database Schema

### Required Tables

```sql
-- Admin users table
CREATE TABLE bread_admin (
    bread_admin_id INT AUTO_INCREMENT PRIMARY KEY,
    bread_admin_username VARCHAR(50) UNIQUE NOT NULL,
    bread_admin_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Regular users table
CREATE TABLE bread_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    full_name VARCHAR(100),
    phone VARCHAR(20),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Menu items table
CREATE TABLE bread_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    item_description TEXT,
    item_price DECIMAL(10,2) NOT NULL,
    item_type ENUM('appetizer', 'main_course', 'dessert', 'beverage', 'special'),
    item_image VARCHAR(255),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE bread_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10,2),
    order_status ENUM('pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES bread_users(user_id)
);
```

## Usage

### Default Admin Login
- Create an admin user in the `bread_admin` table with a hashed password
- Use MD5 hashing for password storage (matches existing PHP system)

### Features Overview

1. **Dashboard**
   - View total users, items, orders, and pending orders
   - Quick action buttons for common tasks
   - System status indicators

2. **User Management**
   - View all registered users
   - Search and filter functionality
   - User status management

3. **Menu Management**
   - Add new menu items with categories
   - Edit existing items
   - Delete items with confirmation
   - Image URL support with preview
   - Category filtering and search

4. **Order Management**
   - View all orders with customer details
   - Update order status with dropdown
   - Filter by order status
   - Search orders by customer or order ID

## Project Structure

```
admin_flask/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── run.py               # Application runner
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── README.md           # This file
├── templates/          # Jinja2 templates
│   ├── base.html       # Base template
│   ├── admin_layout.html # Admin layout
│   ├── login.html      # Login page
│   ├── dashboard.html  # Dashboard
│   ├── users.html      # User management
│   ├── items.html      # Item listing
│   ├── add_item.html   # Add item form
│   ├── edit_item.html  # Edit item form
│   └── orders.html     # Order management
└── static/            # Static files (CSS, JS, images)
    ├── css/
    └── js/
```

## Security Notes

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive configuration
- Implement proper password hashing (consider upgrading from MD5)
- Add CSRF protection for forms
- Implement rate limiting for login attempts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Bread and Butter restaurant management system.