import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'config.dart'; // Ensure baseUrl and imageUrl are defined here
import 'profile.dart';
import 'menu.dart';
import 'offers.dart';
import 'cart.dart';
import 'models/recommendation.dart'; // Add this line

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _textSlideAnimation;
  late Animation<Offset> _imageSlideAnimation;
  late Animation<double> _fadeAnimation;

  final PageController _pageController = PageController(); // Add PageController
  int _currentPageIndex = 0; // Track the current page index
  int _currentIndex = 0; // For bottom navigation

  // List to store recommended items details
  List<Recommendation> _recommendedItems = []; // Changed from List<dynamic>
  bool _isLoadingRecommendations = true;

  // User data
  String _username = '';
  bool _isLoadingUsername = true;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..forward();

    // For text (slide in from right)
    _textSlideAnimation = Tween<Offset>(
      begin: const Offset(1, 0),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    // For images (slide in from left)
    _imageSlideAnimation = Tween<Offset>(
      begin: const Offset(-1, 0),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    // Fetch user data and recommendations when screen initializes
    _fetchUserData();
    _fetchRecommendations();
  }

  Future<void> _fetchUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final username = prefs.getString('username');
      if (username != null) {
        setState(() {
          _username = username;
          _isLoadingUsername = false;
        });
      } else {
        setState(() {
          _username = 'User';
          _isLoadingUsername = false;
        });
      }
    } catch (e) {
      print('Error fetching user data: $e');
      setState(() {
        _username = 'User';
        _isLoadingUsername = false;
      });
    }
  }

  Future<void> _fetchRecommendations() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null) {
      print('Token is not available');
      setState(() => _isLoadingRecommendations = false);
      return;
    }

    try {
      // Updated URL to match the Python Backend Route
      final response = await http.get(
        Uri.parse('$baseUrl/recommendations'), 
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Gemini returns { "recommendations": [...] }
        // We use the '?? []' to ensure it doesn't crash if null
        final List<dynamic> rawList = data['recommendations'] ?? [];

        setState(() {
          // Map the JSON directly to our Recommendation Model
          _recommendedItems = rawList.map((item) => Recommendation.fromJson(item)).toList();
          _isLoadingRecommendations = false;
        });
      } else {
        print('Failed to load recommendations: ${response.statusCode}');
        setState(() => _isLoadingRecommendations = false);
      }
    } catch (e) {
      print('Error fetching recommendations: $e');
      setState(() => _isLoadingRecommendations = false);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _pageController.dispose(); // Dispose PageController
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      body: CustomScrollView(
        slivers: [
          _buildSliverAppBar(),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 24),
                  _buildAnimatedImage(_buildSpecialOffers()),
                  const SizedBox(height: 12),
                  _buildAnimatedText(_buildCarouselIndicators()),
                  const SizedBox(height: 32),
                  _buildAnimatedText(_buildSectionTitle('Recommended For You', Icons.restaurant_menu_rounded)),
                  const SizedBox(height: 16),
                  _buildAnimatedImage(_buildRecommendationsWidget()),
                  const SizedBox(height: 32),
                  _buildAnimatedText(_buildSectionTitle("This Week's Special", Icons.local_fire_department_rounded)),
                  const SizedBox(height: 16),
                  _buildAnimatedImage(_buildHighlightContainer()),
                  const SizedBox(height: 120),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  // Text fade-in from right
  Widget _buildAnimatedText(Widget child) {
    return SlideTransition(
      position: _imageSlideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: child,
      ),
    );
  }

  // Images fade-in from left
  Widget _buildAnimatedImage(Widget child) {
    return SlideTransition(
      position: _textSlideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: child,
      ),
    );
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      floating: true,
      snap: true,
      pinned: false,
      expandedHeight: 120,
      automaticallyImplyLeading: false,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Colors.orange.shade600,
                Colors.orange.shade800,
              ],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Good ${_getGreeting()}!',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            _isLoadingUsername ? 'User' : _username,
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: IconButton(
                          icon: Icon(Icons.person_rounded, color: Colors.white, size: 20),
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => ProfileScreen()),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
  }

  Widget _buildSpecialOffers() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              "Today's Special Offers",
              style: TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 20,
                color: Colors.grey.shade800,
              ),
            ),
            TextButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => OffersPage()),
                );
              },
              child: Text(
                'View All',
                style: TextStyle(
                  color: Colors.orange.shade600,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 160,
          child: PageView(
            controller: _pageController,
            onPageChanged: (index) {
              setState(() {
                _currentPageIndex = index;
              });
            },
            children: [
              _buildSpecialOfferImage('assets/offer2.jpg'),
              _buildSpecialOfferImage('assets/offer1.jpg'),
              _buildSpecialOfferImage('assets/offer3.jpg'),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSpecialOfferImage(String imagePath) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
        image: DecorationImage(
          image: AssetImage(imagePath),
          fit: BoxFit.cover,
        ),
      ),
    );
  }

  Widget _buildCarouselIndicators() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        return AnimatedContainer(
          duration: Duration(milliseconds: 300),
          margin: EdgeInsets.symmetric(horizontal: 4),
          width: index == _currentPageIndex ? 24 : 8,
          height: 8,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            color: index == _currentPageIndex
                ? Colors.orange.shade600
                : Colors.grey.shade300,
          ),
        );
      }),
    );
  }

  Widget _buildSectionTitle(String title, IconData icon) {
    return Row(
      children: [
        Container(
          padding: EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.orange.shade600.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            icon,
            color: Colors.orange.shade600,
            size: 20,
          ),
        ),
        SizedBox(width: 12),
        Text(
          title,
          style: TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 20,
            color: Colors.grey.shade800,
          ),
        ),
      ],
    );
  }

  Widget _buildRecommendationsWidget() {
    if (_isLoadingRecommendations) {
      return Container(
        height: 240, // Increased height for the new card style
        child: Center(
          child: CircularProgressIndicator(color: Colors.orange.shade600),
        ),
      );
    } else if (_recommendedItems.isEmpty) {
      // ... (Your existing empty state code is fine, or use this simple one)
      return Container(
        height: 180,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Center(child: Text('Order to get AI picks!')),
      );
    } else {
      return SizedBox(
        height: 250, // Height to fit Image + Name + Reason
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          itemCount: _recommendedItems.length,
          itemBuilder: (context, index) {
            final item = _recommendedItems[index];
            return Container(
              width: 180, // Slightly wider for better text reading
              margin: const EdgeInsets.only(right: 16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.08),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. IMAGE SECTION
                  // 1. IMAGE SECTION WITH PRICE TAG
                  Expanded(
                    flex: 3,
                    child: Stack(
                      children: [
                        // The Background Image
                        Container(
                          decoration: BoxDecoration(
                            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                            image: DecorationImage(
                              image: item.imageUrl != null
                                  ? NetworkImage(item.imageUrl!)
                                  : const AssetImage('assets/placeholder.png') as ImageProvider,
                              fit: BoxFit.cover,
                            ),
                          ),
                        ),
                        
                        // The Price Tag (Top Right Corner)
                        Positioned(
                          top: 8,
                          right: 8,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.7),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '\$${item.price.toStringAsFixed(2)}', // Display as $12.99
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  // 2. TEXT DETAILS SECTION
                  Expanded(
                    flex: 2,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Item Name
                          Text(
                            item.name,
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: Colors.grey.shade800,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 6),
                          
                          // AI "Reason" Text - The key feature!
                          Text(
                            item.reason,
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.orange.shade800,
                              fontStyle: FontStyle.italic,
                              height: 1.2,
                            ),
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      );
    }
  }

  Widget _buildHighlightContainer() {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => MenuPage()),
        );
      },
      child: Container(
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.15),
              blurRadius: 20,
              offset: Offset(0, 8),
            ),
          ],
        ),
        child: Stack(
          children: [
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Colors.orange.shade400,
                    Colors.orange.shade700,
                  ],
                ),
              ),
            ),
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                image: DecorationImage(
                  image: AssetImage('assets/special.jpg'),
                  fit: BoxFit.cover,
                  colorFilter: ColorFilter.mode(
                    Colors.black.withOpacity(0.3),
                    BlendMode.overlay,
                  ),
                ),
              ),
            ),
            Positioned(
              left: 24,
              bottom: 24,
              right: 24,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.9),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      'LIMITED TIME',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: Colors.orange.shade700,
                        letterSpacing: 1,
                      ),
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Chef\'s Special Menu',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Try our exclusive weekly dishes',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.9),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            Positioned(
              top: 16,
              right: 16,
              child: Container(
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.arrow_forward_rounded,
                  color: Colors.white,
                  size: 20,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNavigationBar() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 20,
            offset: Offset(0, -5),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(0, Icons.home_rounded, 'Home', () {
                // Already on home, do nothing or refresh
              }),
              _buildNavItem(1, Icons.local_offer_rounded, 'Offers', () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => OffersPage()),
                );
              }),
              _buildNavItem(2, Icons.restaurant_menu_rounded, 'Menu', () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => MenuPage()),
                );
              }),
              _buildNavItem(3, Icons.shopping_bag_rounded, 'Cart', () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => CartPage()),
                );
              }),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label, VoidCallback onTap) {
    bool isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () {
        if (_currentIndex != index) {
          setState(() {
            _currentIndex = index;
          });
          onTap();
        }
      },
      child: AnimatedContainer(
        duration: Duration(milliseconds: 200),
        padding: EdgeInsets.symmetric(
          horizontal: isSelected ? 16 : 8,
          vertical: 8,
        ),
        decoration: BoxDecoration(
          color: isSelected ? Colors.orange.shade600 : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? Colors.white : Colors.grey.shade600,
              size: 24,
            ),
            SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                color: isSelected ? Colors.white : Colors.grey.shade600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}