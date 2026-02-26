import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'config.dart';
import 'profile.dart';
import 'menu.dart';
import 'offers.dart';
import 'cart.dart';
import 'models/recommendation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _textSlideAnimation;
  late Animation<Offset> _imageSlideAnimation;
  late Animation<double> _fadeAnimation;

  final PageController _pageController = PageController();
  int _currentPageIndex = 0;
  int _currentIndex = 0;

  List<Recommendation> _recommendedItems = [];
  bool _isLoadingRecommendations = true;
  String _username = '';
  bool _isLoadingUsername = true;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..forward();

    _textSlideAnimation = Tween<Offset>(
            begin: const Offset(1, 0), end: Offset.zero)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _imageSlideAnimation = Tween<Offset>(
            begin: const Offset(-1, 0), end: Offset.zero)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _fadeAnimation = Tween<double>(begin: 0, end: 1)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _fetchUserData();
    _fetchRecommendations();
  }

  Future<void> _fetchUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final username = prefs.getString('username');
      setState(() {
        _username = username ?? 'User';
        _isLoadingUsername = false;
      });
    } catch (e) {
      setState(() {
        _username = 'User';
        _isLoadingUsername = false;
      });
    }
  }

  Future<void> _fetchRecommendations() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null || token.isEmpty) {
      setState(() => _isLoadingRecommendations = false);
      return;
    }

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/recommendations'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> rawList = data['recommendations'] ?? [];

        setState(() {
          _recommendedItems =
              rawList.map((item) => Recommendation.fromJson(item)).toList();
          _isLoadingRecommendations = false;
        });
      } else {
        setState(() => _isLoadingRecommendations = false);
      }
    } catch (e) {
      setState(() => _isLoadingRecommendations = false);
    }
  }

  // 📈 NEW: Send Reinforcement Learning Feedback (+1.0 for tap, -1.0 for unlike)
  Future<void> _sendRLFeedback(
      String itemId, String? category, double reward) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null) return;

    try {
      await http.post(
        Uri.parse('$baseUrl/feedback'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode({
          'item_id': itemId,
          'category': category ?? 'General',
          'reward': reward,
        }),
      );
      print('DEBUG: RL Reward $reward sent for $itemId');
    } catch (e) {
      print('DEBUG: RL Error: $e');
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _pageController.dispose();
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
                  _buildAnimatedText(_buildSectionTitle(
                      'Recommended For You', Icons.restaurant_menu_rounded)),
                  const SizedBox(height: 16),
                  _buildAnimatedImage(_buildRecommendationsWidget()),
                  const SizedBox(height: 32),
                  _buildAnimatedText(_buildSectionTitle("This Week's Special",
                      Icons.local_fire_department_rounded)),
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

  Widget _buildRecommendationsWidget() {
    if (_isLoadingRecommendations) {
      return SizedBox(
        height: 220,
        child: Center(
            child: CircularProgressIndicator(color: Colors.orange.shade600)),
      );
    } else if (_recommendedItems.isEmpty) {
      return Container(
        height: 150,
        width: double.infinity,
        decoration: BoxDecoration(
            color: Colors.white, borderRadius: BorderRadius.circular(16)),
        child: const Center(
            child: Text('Order something to get AI picks!',
                style: TextStyle(color: Colors.grey))),
      );
    } else {
      return SizedBox(
        height: 220,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          itemCount: _recommendedItems.length,
          itemBuilder: (context, index) {
            final item = _recommendedItems[index];
            return Stack(
              children: [
                GestureDetector(
                  onTap: () {
                    // 📈 POSITIVE REWARD: User showed interest
                    _sendRLFeedback(item.itemId, item.category, 1.0);

                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context) =>
                              MenuPage(highlightItemId: item.itemId)),
                    );
                  },
                  child: Container(
                    width: 160,
                    margin: const EdgeInsets.only(right: 16, bottom: 10),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                            color: Colors.black.withOpacity(0.08),
                            blurRadius: 10,
                            offset: const Offset(0, 4)),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          flex: 5,
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(16)),
                              image: DecorationImage(
                                image: (item.imageUrl != null &&
                                        item.imageUrl!.startsWith('http'))
                                    ? NetworkImage(item.imageUrl!)
                                    : const AssetImage('assets/placeholder.png')
                                        as ImageProvider,
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(item.name,
                                  style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.grey.shade800),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis),
                              const SizedBox(height: 4),
                              Text('\$${item.price.toStringAsFixed(2)}',
                                  style: TextStyle(
                                      color: Colors.orange.shade700,
                                      fontWeight: FontWeight.w700,
                                      fontSize: 12)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                // 📉 NEGATIVE REWARD: Unlike Button
                Positioned(
                  top: 8,
                  left: 8,
                  child: GestureDetector(
                    onTap: () {
                      _sendRLFeedback(item.itemId, item.category, -1.0);
                      setState(() {
                        _recommendedItems.removeAt(index);
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                          color: Colors.black54, shape: BoxShape.circle),
                      child: const Icon(Icons.close,
                          color: Colors.white, size: 14),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      );
    }
  }

  // --- UI HELPER METHODS ---

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      floating: true,
      expandedHeight: 120,
      automaticallyImplyLeading: false,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Colors.orange.shade600, Colors.orange.shade800],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Good ${_getGreeting()}!',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 14)),
                      Text(_isLoadingUsername ? 'User' : _username,
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.w700)),
                    ],
                  ),
                  CircleAvatar(
                    backgroundColor: Colors.white.withOpacity(0.2),
                    child: IconButton(
                      icon:
                          const Icon(Icons.person_rounded, color: Colors.white),
                      onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                              builder: (context) => ProfileScreen())),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSpecialOffers() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text("Today's Special Offers",
                style: TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 20,
                    color: Colors.grey.shade800)),
            TextButton(
              onPressed: () => Navigator.push(context,
                  MaterialPageRoute(builder: (context) => const OffersPage())),
              child: Text('View All',
                  style: TextStyle(
                      color: Colors.orange.shade600,
                      fontWeight: FontWeight.w600)),
            ),
          ],
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 160,
          child: PageView(
            controller: _pageController,
            onPageChanged: (index) => setState(() => _currentPageIndex = index),
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
        image: DecorationImage(image: AssetImage(imagePath), fit: BoxFit.cover),
      ),
    );
  }

  Widget _buildCarouselIndicators() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.symmetric(horizontal: 4),
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
        Icon(icon, color: Colors.orange.shade600, size: 20),
        const SizedBox(width: 12),
        Text(title,
            style: TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 20,
                color: Colors.grey.shade800)),
      ],
    );
  }

  Widget _buildHighlightContainer() {
    return GestureDetector(
      onTap: () => Navigator.push(
          context, MaterialPageRoute(builder: (context) => const MenuPage())),
      child: Container(
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          image: const DecorationImage(
              image: AssetImage('assets/special.jpg'), fit: BoxFit.cover),
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            gradient: LinearGradient(
                colors: [Colors.black.withOpacity(0.6), Colors.transparent],
                begin: Alignment.bottomLeft),
          ),
          padding: const EdgeInsets.all(20),
          child: const Column(
              mainAxisAlignment: MainAxisAlignment.end,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Chef\'s Special Menu',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold)),
                Text('Try our exclusive weekly dishes',
                    style: TextStyle(color: Colors.white70)),
              ]),
        ),
      ),
    );
  }

  Widget _buildBottomNavigationBar() {
    return BottomNavigationBar(
      currentIndex: _currentIndex,
      onTap: (index) {
        setState(() => _currentIndex = index);
        if (index == 1)
          Navigator.push(context,
              MaterialPageRoute(builder: (context) => const OffersPage()));
        if (index == 2)
          Navigator.push(context,
              MaterialPageRoute(builder: (context) => const MenuPage()));
        if (index == 3)
          Navigator.push(
              context, MaterialPageRoute(builder: (context) => CartPage()));
      },
      selectedItemColor: Colors.orange.shade600,
      unselectedItemColor: Colors.grey,
      type: BottomNavigationBarType.fixed,
      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.home_rounded), label: 'Home'),
        BottomNavigationBarItem(
            icon: Icon(Icons.local_offer_rounded), label: 'Offers'),
        BottomNavigationBarItem(
            icon: Icon(Icons.restaurant_menu_rounded), label: 'Menu'),
        BottomNavigationBarItem(
            icon: Icon(Icons.shopping_bag_rounded), label: 'Cart'),
      ],
    );
  }

  Widget _buildAnimatedText(Widget child) => SlideTransition(
      position: _imageSlideAnimation,
      child: FadeTransition(opacity: _fadeAnimation, child: child));
  Widget _buildAnimatedImage(Widget child) => SlideTransition(
      position: _textSlideAnimation,
      child: FadeTransition(opacity: _fadeAnimation, child: child));
}
