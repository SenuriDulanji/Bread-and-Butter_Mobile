import 'orders.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'menu.dart';
import 'config.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(MaterialApp(
    home: CartPage(),
  ));
}

class CartPage extends StatefulWidget {
  @override
  _CartPageState createState() => _CartPageState();
}

class _CartPageState extends State<CartPage> {
  List<CartItemData> cartItems = [];

  @override
  void initState() {
    super.initState();
    _loadCart();
  }

  Future<void> placeOrder() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('userId'); // Retrieve user ID

    if (userId == null) {
      print('User ID is not available');
      return;
    }

    // Prepare order data with proper format for backend
    List<Map<String, dynamic>> orderItems = cartItems.map((item) {
      return {
        'item_id': item.itemId,
        'name': item.title,
        'price': item.price,
        'quantity': item.quantity,
        'total': item.price * item.quantity,
      };
    }).toList();

    Map<String, dynamic> orderData = {
      'total_amount': calculateTotal(),
      'items': orderItems,
      'delivery_address': '',  // Can be added later with address functionality
      'phone': '',  // Can be added later with phone functionality
    };

    // Convert order data to JSON
    String jsonOrderData = json.encode(orderData);

    // Log the request being sent
    print('Sending order data: $jsonOrderData');

    try {
      // Get JWT token from shared preferences
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token') ?? '';
      
      final response = await http.post(
        Uri.parse('$baseUrl/add_order'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonOrderData,
      );

      // Log the raw response body
      print('Server response (${response.statusCode}): ${response.body}');

      if (response.statusCode == 200) {
        var responseData = json.decode(response.body);
        if (responseData['success'] == true) {
          // Clear the cart after a successful order
          setState(() {
            cartItems.clear();
          });

          // Remove the saved cart from SharedPreferences
          await prefs.remove('cart');
          print('Order placed successfully');

          // Navigate to MyOrdersScreen
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => MyOrdersScreen()),
          );
        }
        else {
          print('Order failed: ${responseData['message']}');
        }
      } else {
        print('Failed to place order. HTTP Status: ${response.statusCode}');
      }
    } catch (e) {
      print('Error placing order: $e');
    }
  }

  // Load cart from SharedPreferences
  Future<void> _loadCart() async {
    final prefs = await SharedPreferences.getInstance();
    List<String> savedCartItems = prefs.getStringList('cart') ?? [];

    // Debug log to check if the cart is loaded correctly
    print('Cart loaded from SharedPreferences: $savedCartItems');

    setState(() {
      // Deserialize cart items from the list of JSON strings
      cartItems = savedCartItems.map((item) => CartItemData.fromJson(json.decode(item))).toList();
    });

    // Debug log to check if the cartItems list is updated correctly
    print('Cart items after loading: ${cartItems.map((item) => item.itemId).toList()}');
  }

  // Save cart to SharedPreferences
  Future<void> _saveCart() async {
    final prefs = await SharedPreferences.getInstance();
    List<String> savedCartItems = cartItems.map((item) => json.encode(item.toJson())).toList();

    // Debug log to check if the cart is being saved correctly
    print('Saving cart: $savedCartItems');

    await prefs.setStringList('cart', savedCartItems);

    // Log the saved cart after saving
    print('Cart saved to SharedPreferences: ${prefs.getStringList('cart')}');
  }

  // Function to calculate the total price
  double calculateTotal() {
    double total = 0;
    for (var item in cartItems) {
      total += item.price * item.quantity;
    }
    return total;
  }

  // Function to update quantity for a cart item
  void updateQuantity(int index, int change) {
    setState(() {
      cartItems[index].quantity += change;
      if (cartItems[index].quantity < 1) {
        cartItems[index].quantity = 1; // Prevent quantity from going below 1
      }
    });
    _saveCart();
  }

  // Function to remove an item from the cart
  void removeItem(int index) {
    setState(() {
      cartItems.removeAt(index);
    });
    _saveCart();
  }

  @override
  Widget build(BuildContext context) {
    double totalPrice = calculateTotal(); // Calculate the total price

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.close, color: Colors.orange.shade900),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: Text(
          'My Cart',
          style: TextStyle(color: Colors.orange.shade900),
        ),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            _buildFreeShippingBanner(),
            SizedBox(height: 16),
            
            // Cart Items or Empty State
            Expanded(
              child: cartItems.isEmpty
                  ? _buildEmptyCartState()
                  : ListView.builder(
                      padding: EdgeInsets.symmetric(horizontal: 4.0),
                      itemCount: cartItems.length,
                      itemBuilder: (context, index) {
                        return CartItem(
                          imagePath: cartItems[index].imagePath,
                          title: cartItems[index].title,
                          price: cartItems[index].price,
                          quantity: cartItems[index].quantity,
                          onRemove: () => removeItem(index),
                          onIncrease: () => updateQuantity(index, 1),
                          onDecrease: () => updateQuantity(index, -1),
                        );
                      },
                    ),
            ),
            
            // Bottom Section
            if (cartItems.isNotEmpty) ...[
              Container(
                margin: EdgeInsets.symmetric(horizontal: 8.0),
                child: Divider(
                  thickness: 1,
                  color: Colors.grey.shade300,
                ),
              ),
              _buildTotalSection(totalPrice),
              SizedBox(height: 16),
              _buildCheckoutButton(),
              SizedBox(height: 8),
            ],
            _buildContinueShoppingButton(context),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyCartState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              color: Colors.orange.shade50,
              borderRadius: BorderRadius.circular(60),
            ),
            child: Icon(
              Icons.shopping_cart_outlined,
              size: 60,
              color: Colors.orange.shade300,
            ),
          ),
          SizedBox(height: 24),
          Text(
            'Your cart is empty',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w600,
              color: Colors.grey.shade700,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Add some delicious items from our menu\nto get started!',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade500,
              height: 1.4,
            ),
          ),
          SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => MenuPage()),
              );
            },
            icon: Icon(Icons.restaurant_menu, color: Colors.white),
            label: Text(
              'Browse Menu',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange.shade600,
              padding: EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(25),
              ),
              elevation: 2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFreeShippingBanner() {
    return Container(
      padding: EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [
            Colors.orange.shade50,
            Colors.orange.shade100.withValues(alpha: 0.7),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.orange.shade200,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.orange.shade600,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              Icons.local_offer,
              color: Colors.white,
              size: 20,
            ),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Apply your promo code for extra savings!',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: Colors.orange.shade800,
                fontSize: 15,
              ),
            ),
          ),
          Icon(
            Icons.chevron_right,
            color: Colors.orange.shade600,
            size: 20,
          ),
        ],
      ),
    );
  }

  Widget _buildTotalSection(double totalPrice) {
    return Container(
      padding: EdgeInsets.all(20.0),
      margin: EdgeInsets.symmetric(horizontal: 4.0),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
        border: Border.all(
          color: Colors.orange.shade100,
          width: 1,
        ),
      ),
      child: Column(
        children: [
          // Order Summary
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Items (${cartItems.length})',
                style: TextStyle(
                  fontSize: 15,
                  color: Colors.grey.shade600,
                ),
              ),
              Text(
                '\$${totalPrice.toStringAsFixed(2)}',
                style: TextStyle(
                  fontSize: 15,
                  color: Colors.grey.shade700,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Delivery',
                style: TextStyle(
                  fontSize: 15,
                  color: Colors.grey.shade600,
                ),
              ),
              Text(
                'FREE',
                style: TextStyle(
                  fontSize: 15,
                  color: Colors.green.shade600,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          Divider(color: Colors.grey.shade300),
          SizedBox(height: 12),
          // Total
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Total',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: Colors.grey.shade800,
                ),
              ),
              Text(
                '\$${totalPrice.toStringAsFixed(2)}',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                  color: Colors.orange.shade800,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCheckoutButton() {
    return Container(
      width: double.infinity,
      margin: EdgeInsets.symmetric(horizontal: 4.0),
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.orange.shade600,
          padding: EdgeInsets.symmetric(vertical: 18),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 2,
          shadowColor: Colors.orange.shade200,
        ),
        onPressed: cartItems.isNotEmpty
            ? () {
                placeOrder();
              }
            : null,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.shopping_bag,
              color: Colors.white,
              size: 20,
            ),
            SizedBox(width: 8),
            Text(
              'PLACE ORDER',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Colors.white,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContinueShoppingButton(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: EdgeInsets.symmetric(horizontal: 4.0),
      child: TextButton.icon(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => MenuPage()),
          );
        },
        icon: Icon(
          Icons.restaurant_menu,
          color: Colors.orange.shade600,
          size: 18,
        ),
        label: Text(
          cartItems.isEmpty ? 'BROWSE MENU' : 'CONTINUE SHOPPING',
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            color: Colors.orange.shade600,
            letterSpacing: 0.3,
          ),
        ),
        style: TextButton.styleFrom(
          padding: EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }
}

class CartItemData {
  final int itemId; // New property for the item identifier
  final String imagePath;
  final String title;
  final double price;
  int quantity;

  CartItemData({
    required this.itemId,
    required this.imagePath,
    required this.title,
    required this.price,
    required this.quantity,
  });

  // Convert CartItemData to a JSON map
  Map<String, dynamic> toJson() {
    return {
      'item_id': itemId,
      'imagePath': imagePath,
      'title': title,
      'price': price,
      'quantity': quantity,
    };
  }

  // Create CartItemData from a JSON map with null checks
  factory CartItemData.fromJson(Map<String, dynamic> json) {
    return CartItemData(
      itemId: json['item_id'] ?? 0,
      imagePath: json['imagePath'] ?? '',
      title: json['title'] ?? '',
      price: json['price'] is String ? double.tryParse(json['price']) ?? 0.0 : json['price'] ?? 0.0,
      quantity: json['quantity'] ?? 1,
    );
  }
}

class CartItem extends StatelessWidget {
  final String imagePath;
  final String title;
  final double price;
  final int quantity;
  final VoidCallback onRemove;
  final VoidCallback onIncrease;
  final VoidCallback onDecrease;

  const CartItem({
    required this.imagePath,
    required this.title,
    required this.price,
    required this.quantity,
    required this.onRemove,
    required this.onIncrease,
    required this.onDecrease,
  });

  String _constructImageUrl(String imagePath) {
    if (imagePath.isEmpty) {
      return '';
    }
    // Handle both full paths and filenames like menu.dart
    if (imagePath.startsWith('uploads/')) {
      return '$imageUrl$imagePath';
    } else {
      return '${imageUrl}uploads/images/$imagePath';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: 16.0),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16.0),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 12.0,
            offset: Offset(0, 4),
            spreadRadius: 0,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16.0),
        child: Column(
          children: [
            // Main content area
            Padding(
              padding: EdgeInsets.all(16.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Product Image
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12.0),
                      color: Colors.orange.shade50,
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12.0),
                      child: imagePath.isNotEmpty 
                          ? Image.network(
                              _constructImageUrl(imagePath),
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) {
                                return Icon(
                                  Icons.fastfood,
                                  size: 40,
                                  color: Colors.orange.shade300,
                                );
                              },
                              loadingBuilder: (context, child, loadingProgress) {
                                if (loadingProgress == null) return child;
                                return Center(
                                  child: CircularProgressIndicator(
                                    color: Colors.orange.shade300,
                                    strokeWidth: 2.0,
                                  ),
                                );
                              },
                            )
                          : Icon(
                              Icons.fastfood,
                              size: 40,
                              color: Colors.orange.shade300,
                            ),
                    ),
                  ),
                  
                  SizedBox(width: 16),
                  
                  // Product Details
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Title and Remove Button Row
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                title,
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 17,
                                  color: Colors.grey.shade800,
                                  height: 1.3,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            // Remove Button
                            GestureDetector(
                              onTap: onRemove,
                              child: Container(
                                padding: EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: Colors.red.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(
                                  Icons.delete_outline,
                                  color: Colors.red.shade400,
                                  size: 20,
                                ),
                              ),
                            ),
                          ],
                        ),
                        
                        SizedBox(height: 12),
                        
                        // Price
                        Text(
                          '\$${price.toStringAsFixed(2)}',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: Colors.orange.shade800,
                          ),
                        ),
                        
                        SizedBox(height: 4),
                        
                        // Unit price indicator
                        Text(
                          'per item',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            // Bottom Section with Quantity Controls and Total
            Container(
              padding: EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                border: Border(
                  top: BorderSide(
                    color: Colors.grey.shade200,
                    width: 1,
                  ),
                ),
              ),
              child: Row(
                children: [
                  // Quantity Label
                  Text(
                    'Quantity',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  
                  Spacer(),
                  
                  // Quantity Controls
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(25),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 4,
                          offset: Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Decrease Button
                        GestureDetector(
                          onTap: quantity > 1 ? onDecrease : null,
                          child: Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: quantity > 1 ? Colors.orange.shade600 : Colors.grey.shade300,
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Icon(
                              Icons.remove,
                              color: Colors.white,
                              size: 18,
                            ),
                          ),
                        ),
                        
                        // Quantity Display
                        Container(
                          width: 50,
                          child: Text(
                            '$quantity',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 16,
                              color: Colors.grey.shade800,
                            ),
                          ),
                        ),
                        
                        // Increase Button
                        GestureDetector(
                          onTap: onIncrease,
                          child: Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: Colors.orange.shade600,
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Icon(
                              Icons.add,
                              color: Colors.white,
                              size: 18,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  SizedBox(width: 16),
                  
                  // Item Total
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Total',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade500,
                        ),
                      ),
                      Text(
                        '\$${(price * quantity).toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: Colors.orange.shade800,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
