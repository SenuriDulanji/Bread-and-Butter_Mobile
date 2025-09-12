import 'package:flutter/material.dart';
import 'cart.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'config.dart';

class MenuPage extends StatefulWidget {
  @override
  _MenuPageState createState() => _MenuPageState();
}

class _MenuPageState extends State<MenuPage> {
  List<Map<String, dynamic>> menuItems = [];
  List<Map<String, dynamic>> allMenuItems = [];
  List<Map<String, dynamic>> categories = [];
  String selectedFilter = "All"; // Default filter
  int? selectedCategoryId; // Track selected category ID
  TextEditingController searchController = TextEditingController();

  // Function to fetch categories from API
  Future<void> fetchCategories() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/categories'));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        if (data['success'] == true) {
          setState(() {
            categories = List<Map<String, dynamic>>.from(data['categories']);
          });
        } else {
          print('Failed to fetch categories: ${data['message']}');
        }
      } else {
        print('Failed to load categories. HTTP status: ${response.statusCode}');
      }
    } catch (error) {
      print('Error fetching categories: $error');
    }
  }

  // Function to fetch menu items from API
  Future<void> fetchMenuItems() async {
    try {
      // Build URL based on filter: if "All", do not include parameter
      String url = '$baseUrl/fetch_items';
      if (selectedFilter != "All" && selectedCategoryId != null) {
        url += '?category_id=$selectedCategoryId';
      }
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        if (data['success'] == true) {
          // Save the fetched items locally
          allMenuItems = List<Map<String, dynamic>>.from(data['items']);
          // Apply any current search filter
          filterMenuItems(searchController.text);
        } else {
          print('Failed to fetch items: ${data['message']}');
        }
      } else {
        print('Failed to load data. HTTP status: ${response.statusCode}');
      }
    } catch (error) {
      print('Error fetching menu items: $error');
    }
  }

  // Filter the locally loaded items based on the search query
  void filterMenuItems(String query) {
    List<Map<String, dynamic>> filteredItems;
    if (query.isEmpty) {
      filteredItems = List<Map<String, dynamic>>.from(allMenuItems);
    } else {
      filteredItems = allMenuItems.where((item) {
        final itemName = item['name'].toString().toLowerCase();
        return itemName.contains(query.toLowerCase());
      }).toList();
    }
    setState(() {
      menuItems = filteredItems;
    });
  }

  // Save item to cart using SharedPreferences
  Future<void> addToCart(Map<String, dynamic> item) async {
    final prefs = await SharedPreferences.getInstance();
    List<String> cartItems = prefs.getStringList('cart') ?? [];

    bool itemExists = false;

    for (int i = 0; i < cartItems.length; i++) {
      Map<String, dynamic> cartItem = json.decode(cartItems[i]);

      // Check if the item already exists in the cart
      if (cartItem['item_id'] == item['id']) {
        // Item exists, update its quantity
        cartItem['quantity']++;
        cartItems[i] = json.encode(cartItem);
        itemExists = true;
        break;
      }
    }

    // If item doesn't exist, add it as a new item
    if (!itemExists) {
      item['quantity'] = 1;
      item['item_id'] = item['id'];
      item['imagePath'] = item['image'];
      item['title'] = item['name'];
      cartItems.add(json.encode(item));
    }

    await prefs.setStringList('cart', cartItems);
    print('Cart saved to SharedPreferences: $cartItems');
  }

  @override
  void initState() {
    super.initState();
    fetchCategories(); // Fetch categories first
    fetchMenuItems(); // Fetch items when the page loads
    // Listen for changes in the search field to filter items locally
    searchController.addListener(() {
      filterMenuItems(searchController.text);
    });
  }

  // Update filter and refresh items, also clear search field
  void updateFilter(String filter, int? categoryId) {
    setState(() {
      selectedFilter = filter;
      selectedCategoryId = categoryId;
      searchController.clear();
      menuItems = [];
      allMenuItems = [];
    });
    fetchMenuItems();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.orange.shade50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.arrow_back_rounded, color: Colors.orange.shade700, size: 20),
          ),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: Text(
          'Our Menu',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: Colors.grey.shade800,
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.orange.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(Icons.shopping_bag_outlined, color: Colors.orange.shade700, size: 20),
            ),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => CartPage()),
              );
            },
          ),
          SizedBox(width: 8),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.all(20.0),
            sliver: SliverToBoxAdapter(
              child: Column(
                children: [
                  // Enhanced search field
                  Container(
                    height: 56,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.05),
                          blurRadius: 10,
                          offset: Offset(0, 4),
                        ),
                      ],
                    ),
                    child: TextField(
                      controller: searchController,
                      decoration: InputDecoration(
                        hintText: 'Search for delicious food...',
                        hintStyle: TextStyle(color: Colors.grey.shade500, fontSize: 14),
                        prefixIcon: Padding(
                          padding: EdgeInsets.all(12),
                          child: Icon(Icons.search_rounded, color: Colors.orange.shade600, size: 24),
                        ),
                        suffixIcon: searchController.text.isNotEmpty
                            ? IconButton(
                                icon: Icon(Icons.clear_rounded, color: Colors.grey.shade400, size: 20),
                                onPressed: () {
                                  searchController.clear();
                                  filterMenuItems('');
                                },
                              )
                            : null,
                        filled: true,
                        fillColor: Colors.transparent,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                      ),
                    ),
                  ),
                  SizedBox(height: 20),
                ],
              ),
            ),
          ),
          // Filter chips section
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            sliver: SliverToBoxAdapter(
              child: Container(
                height: 50,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: categories.length + 1, // +1 for "All" option
                  separatorBuilder: (context, index) => SizedBox(width: 12),
                  itemBuilder: (context, index) {
                    if (index == 0) {
                      return _buildFilterChip('All', Icons.apps_rounded, null);
                    } else {
                      final category = categories[index - 1];
                      return _buildFilterChip(
                        category['name'],
                        _getCategoryIcon(category['name']),
                        category['id'],
                      );
                    }
                  },
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: EdgeInsets.only(top: 20),
            sliver: SliverToBoxAdapter(child: Container()),
          ),
          // Menu items list
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            sliver: menuItems.isEmpty
                ? SliverFillRemaining(
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(color: Colors.orange.shade600),
                          SizedBox(height: 16),
                          Text(
                            'Loading delicious food...',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                : SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final item = menuItems[index];
                        return _buildMenuItemCard(item, context);
                      },
                      childCount: menuItems.length,
                    ),
                  ),
          ),
          SliverPadding(
            padding: EdgeInsets.only(bottom: 100),
            sliver: SliverToBoxAdapter(child: Container()),
          ),
        ],
      ),
    );
  }

  // Helper function to get appropriate icon for each category
  IconData _getCategoryIcon(String categoryName) {
    switch (categoryName.toLowerCase()) {
      case 'burgers':
        return Icons.lunch_dining_rounded;
      case 'pizza':
        return Icons.local_pizza_rounded;
      case 'beverages':
        return Icons.local_drink_rounded;
      case 'desserts':
        return Icons.cake_rounded;
      case 'sides':
        return Icons.restaurant_rounded;
      case 'salads':
        return Icons.eco_rounded;
      default:
        return Icons.restaurant_rounded;
    }
  }

  Widget _buildFilterChip(String label, IconData icon, int? categoryId) {
    bool isSelected = selectedFilter == label;
    return GestureDetector(
      onTap: () => updateFilter(label, categoryId),
      child: AnimatedContainer(
        duration: Duration(milliseconds: 200),
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? Colors.orange.shade600 : Colors.white,
          borderRadius: BorderRadius.circular(25),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(isSelected ? 0.15 : 0.05),
              blurRadius: isSelected ? 8 : 4,
              offset: Offset(0, isSelected ? 4 : 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 18,
              color: isSelected ? Colors.white : Colors.grey.shade600,
            ),
            SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                color: isSelected ? Colors.white : Colors.grey.shade700,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItemCard(Map<String, dynamic> item, BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 12,
            offset: Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image section
          Container(
            height: 180,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
              image: item['image'] != null
                  ? DecorationImage(
                      image: NetworkImage(
                        item['image'].toString().startsWith('uploads/')
                            ? '${imageUrl}${item['image']}'
                            : '${imageUrl}uploads/images/${item['image']}',
                      ),
                      fit: BoxFit.cover,
                    )
                  : null,
              color: item['image'] == null ? Colors.orange.shade50 : null,
            ),
            child: item['image'] == null
                ? Center(
                    child: Icon(
                      Icons.fastfood_rounded,
                      size: 60,
                      color: Colors.orange.shade300,
                    ),
                  )
                : Stack(
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              Colors.transparent,
                              Colors.black.withOpacity(0.1),
                            ],
                          ),
                        ),
                      ),
                      Positioned(
                        top: 12,
                        right: 12,
                        child: Container(
                          padding: EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.9),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '\$${item['price']}',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: Colors.orange.shade700,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
          ),
          // Content section
          Padding(
            padding: EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item['name'],
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: Colors.grey.shade800,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  item['description'] ?? 'Delicious food item',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey.shade600,
                    height: 1.4,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                SizedBox(height: 16),
                Row(
                  children: [
                    if (item['image'] == null)
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.orange.shade50,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '\$${item['price']}',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: Colors.orange.shade700,
                          ),
                        ),
                      ),
                    if (item['image'] == null) Spacer(),
                    if (item['image'] != null) Spacer(),
                    GestureDetector(
                      onTap: () {
                        addToCart(item).then((_) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Row(
                                children: [
                                  Icon(Icons.check_circle_rounded, color: Colors.white),
                                  SizedBox(width: 8),
                                  Text('${item['name']} added to cart'),
                                ],
                              ),
                              backgroundColor: Colors.green.shade600,
                              behavior: SnackBarBehavior.floating,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          );
                          Future.delayed(Duration(milliseconds: 500), () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => CartPage()),
                            );
                          });
                        });
                      },
                      child: Container(
                        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.orange.shade600, Colors.orange.shade700],
                          ),
                          borderRadius: BorderRadius.circular(25),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.orange.withOpacity(0.3),
                              blurRadius: 8,
                              offset: Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.add_shopping_cart_rounded,
                              color: Colors.white,
                              size: 18,
                            ),
                            SizedBox(width: 8),
                            Text(
                              'Add to Cart',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}