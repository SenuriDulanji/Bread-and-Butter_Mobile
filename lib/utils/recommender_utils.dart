import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../config.dart'; // Ensure this points to your baseUrl

class RecommenderUtils {
  // 📈 Reward Constants (Weighted Scale)
  static const double rewardClick = 1.0;
  static const double rewardAddToCart = 3.0;
  static const double rewardOrder = 5.0;
  static const double rewardUnlike = -2.0;

  /// Sends the reinforcement learning signal to the backend
  static Future<void> sendFeedback({
    required String itemId,
    required String category,
    required double reward,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null || token.isEmpty) return;

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/feedback'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode({
          'item_id': itemId,
          'category': category,
          'reward': reward,
        }),
      );

      if (response.statusCode == 200) {
        print('✅ RL Sync: Category $category received reward $reward');
      } else {
        print('❌ RL Sync Failed: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ RL Network Error: $e');
    }
  }
}
