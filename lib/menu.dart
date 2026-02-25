import 'package:flutter/material.dart';
import 'cart.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'config.dart';
import 'home.dart';

class MenuPage extends StatefulWidget {
  // 🛠️ Step 1: Accept the highlightItemId from the Home Screen
  final String? highlightItemId;

  const MenuPage({Key? key, this.highlightItemId}) : super(key: key);

  @override
  _MenuPageState createState() => _MenuPageState();
}

class _MenuPageState extends State<MenuPage> {
  List<Map<String, dynamic>> menuItems = [];
  List<Map<String, dynamic>> allMenuItems = [];
  List<Map<String, dynamic>> categories = [];
  String selectedFilter = "All";
  int? selectedCategoryId;
  TextEditingController searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    fetchCategories();
    fetchMenuItems();
    searchController.addListener(() {
      filterMenuItems(searchController.text);
    });
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  Future<void> _onWillPop() async {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  Future<void> fetchCategories() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/categories'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          setState(() {
            categories = List<Map<String, dynamic>>.from(data['categories']);
          });
        }
      }
    } catch (error) {
      print('Error fetching categories: $error');
    }
  }

  Future<void> fetchMenuItems() async {
    try {
      String url = '$baseUrl/fetch_items';
      if (selectedFilter != "All" && selectedCategoryId != null) {
        url += '?category_id=$selectedCategoryId';
      }
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        if (data['success'] == true) {
          List<Map<String, dynamic>> fetchedItems = List<Map<String, dynamic>>.from(data['items']);

          // 🛠️ Step 2: Reorder logic - Move the recommended item to the top
          if (widget.highlightItemId != null && selectedFilter == "All") {
            int index = fetchedItems.indexWhere((item) => 
                item['id'].toString() == widget.highlightItemId.toString());
            
            if (index != -1) {
              final highlightedItem = fetchedItems.removeAt(index);
              // Mark it as highlighted so we can show a badge in the UI
              highlightedItem['isHighlighted'] = true; 
              fetchedItems.insert(0, highlightedItem);
            }
          }

          allMenuItems = fetchedItems;
          filterMenuItems(searchController.text);
        }
      }
    } catch (error) {
      print('Error fetching menu items: $error');
    }
  }

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

  Future<void> addToCart(Map<String, dynamic> item) async {
    final prefs = await SharedPreferences.getInstance();
    List<String> cartItems = prefs.getStringList('cart') ?? [];
    bool itemExists = false;

    for (int i = 0; i < cartItems.length; i++) {
      Map<String, dynamic> cartItem = json.decode(cartItems[i]);
      if (cartItem['item_id'] == item['id']) {
        cartItem['quantity']++;
        cartItems[i] = json.encode(cartItem);
        itemExists = true;
        break;
      }
    }

    if (!itemExists) {
      item['quantity'] = 1;
      item['item_id'] = item['id'];
      item['imagePath'] = item['image'];
      item['title'] = item['name'];
      cartItems.add(json.encode(item));
    }
    await prefs.setStringList('cart', cartItems);
  }

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
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async {
        _onWillPop();
        return false;
      },
      child: Scaffold(
        backgroundColor: Colors.grey.shade50,
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          leading: IconButton(
            icon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: Colors.orange.shade50, borderRadius: BorderRadius.circular(12)),
              child: Icon(Icons.arrow_back_rounded, color: Colors.orange.shade700, size: 20),
            ),
            onPressed: () => _onWillPop(),
          ),
          title: Text('Our Menu', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: Colors.grey.shade800)),
          centerTitle: true,
          actions: [
            IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: Colors.orange.shade50, borderRadius: BorderRadius.circular(12)),
                child: Icon(Icons.shopping_bag_outlined, color: Colors.orange.shade700, size: 20),
              ),
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => CartPage())),
            ),
            const SizedBox(width: 8),
          ],
        ),
        body: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.all(20.0),
              sliver: SliverToBoxAdapter(
                child: Column(
                  children: [
                    Container(
                      height: 56,
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))]),
                      child: TextField(
                        controller: searchController,
                        decoration: InputDecoration(
                          hintText: 'Search for delicious food...',
                          hintStyle: TextStyle(color: Colors.grey.shade500, fontSize: 14),
                          prefixIcon: Icon(Icons.search_rounded, color: Colors.orange.shade600),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              sliver: SliverToBoxAdapter(
                child: SizedBox(
                  height: 50,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: categories.length + 1,
                    separatorBuilder: (context, index) => const SizedBox(width: 12),
                    itemBuilder: (context, index) {
                      if (index == 0) return _buildFilterChip('All', Icons.apps_rounded, null);
                      final cat = categories[index - 1];
                      return _buildFilterChip(cat['name'], _getCategoryIcon(cat['name']), cat['id']);
                    },
                  ),
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.all(20.0),
              sliver: menuItems.isEmpty
                  ? SliverFillRemaining(child: Center(child: CircularProgressIndicator(color: Colors.orange.shade600)))
                  : SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) => _buildMenuItemCard(menuItems[index], context),
                        childCount: menuItems.length,
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  // --- UI COMPONENTS ---

  Widget _buildMenuItemCard(Map<String, dynamic> item, BuildContext context) {
    // 🛠️ Step 3: Check if this item is the one we moved to the top
    bool isHighlighted = item['isHighlighted'] ?? false;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        // Add an orange border if it's the recommended item
        border: isHighlighted ? Border.all(color: Colors.orange.shade400, width: 2) : null,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 12, offset: const Offset(0, 6))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              Container(
                height: 180,
                decoration: BoxDecoration(
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                  image: DecorationImage(
                    image: NetworkImage(
                      item['image'].toString().startsWith('http')
                          ? item['image'].toString()
                          : item['image'].toString().startsWith('uploads/')
                              ? '${imageUrl}${item['image']}'
                              : '${imageUrl}uploads/images/${item['image']}',
                    ),
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              // 🛠️ Step 4: Show a "Recommended" badge on the top item
              if (isHighlighted)
                Positioned(
                  top: 12,
                  left: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(color: Colors.orange.shade600, borderRadius: BorderRadius.circular(12)),
                    child: const Row(
                      children: [
                        Icon(Icons.star_rounded, color: Colors.white, size: 14),
                        SizedBox(width: 4),
                        Text('RECOMMENDED', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10)),
                      ],
                    ),
                  ),
                ),
              Positioned(
                top: 12,
                right: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(color: Colors.white.withOpacity(0.9), borderRadius: BorderRadius.circular(12)),
                  child: Text('\$${item['price']}', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.orange.shade700)),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item['name'], style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colors.grey.shade800)),
                const SizedBox(height: 8),
                Text(item['description'] ?? 'Delicious food item', style: TextStyle(fontSize: 14, color: Colors.grey.shade600, height: 1.4), maxLines: 2, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 16),
                Align(
                  alignment: Alignment.centerRight,
                  child: GestureDetector(
                    onTap: () {
                      addToCart(item).then((_) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${item['name']} added to cart'), backgroundColor: Colors.green.shade600));
                        Navigator.push(context, MaterialPageRoute(builder: (context) => CartPage()));
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      decoration: BoxDecoration(gradient: LinearGradient(colors: [Colors.orange.shade600, Colors.orange.shade700]), borderRadius: BorderRadius.circular(25)),
                      child: const Text('Add to Cart', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // --- Helper Icons and Chips ---
  IconData _getCategoryIcon(String name) {
    if (name.toLowerCase() == 'burgers') return Icons.lunch_dining_rounded;
    if (name.toLowerCase() == 'pizza') return Icons.local_pizza_rounded;
    return Icons.restaurant_rounded;
  }

  Widget _buildFilterChip(String label, IconData icon, int? categoryId) {
    bool isSelected = selectedFilter == label;
    return GestureDetector(
      onTap: () => updateFilter(label, categoryId),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(color: isSelected ? Colors.orange.shade600 : Colors.white, borderRadius: BorderRadius.circular(25)),
        child: Row(children: [
          Icon(icon, size: 18, color: isSelected ? Colors.white : Colors.grey.shade600),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500, color: isSelected ? Colors.white : Colors.grey.shade700)),
        ]),
      ),
    );
  }
}