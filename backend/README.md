# Bread & Butter Flask Backend

This is the Flask backend for the Bread & Butter food delivery mobile application. It provides REST API endpoints for the Flutter mobile app.

## Features

- **REST API** for Flutter mobile app
- **JWT Authentication** for secure API access
- **SQLite Database** with SQLAlchemy ORM
- **CORS Support** for cross-origin requests

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```
   
   Or use the run script:
   ```bash
   python run.py
   ```

The server will start on `http://localhost:5002`


## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/register` - User registration
- `POST /api/verify` - Verify OTP
- `POST /api/resend_otp` - Resend OTP
- `POST /api/reset_pw` - Reset password
- `POST /api/verify_reset_pw` - Verify password reset

### Menu & Items
- `GET /api/fetch_items` - Get menu items (with optional category filter and search)

### Orders
- `POST /api/add_order` - Place an order (requires JWT)
- `GET /api/get_orders` - Get user orders (requires JWT)

### Loyalty & Offers
- `GET /api/get_loyalty_points` - Get user loyalty points (requires JWT)
- `GET /api/get_weekly_highlight` - Get current offers

## Database Models

- **User** - User accounts with authentication and loyalty points
- **Category** - Menu categories
- **MenuItem** - Food items with pricing and availability
- **Order** - Order records with items and status
- **Offer** - Promotional offers and discounts

## JWT Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Configuration

The Flask app uses the following configuration:
- **Database**: SQLite (`breadandbutter.db`)
- **Port**: 5002
- **Host**: 0.0.0.0 (accessible from Android emulator)
- **JWT Token Expiry**: 30 days

## Sample Data

The application automatically creates sample data on first run:
- Sample categories (Burgers, Pizza, Beverages, Desserts)
- Sample menu items
- Sample promotional offers

## Development

For development, the app runs in debug mode with hot reloading enabled. The database file will be created automatically on first run.

## Flutter Integration

The Flutter app is configured to connect to this backend using:
- Base URL: `http://10.0.2.2:5002/api` (for Android emulator)
- Image URL: `http://10.0.2.2:5002/` (for static file serving)

Make sure to start this Flask backend before running the Flutter application.