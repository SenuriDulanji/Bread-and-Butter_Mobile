class Recommendation {
  final String itemId;
  final String name;
  final String category; // Essential for Reinforcement Learning
  final double price;
  final String? imageUrl;

  Recommendation({
    required this.itemId,
    required this.name,
    required this.category,
    required this.price,
    this.imageUrl,
  });

  // This converts the JSON from your Flask API into this Dart object
  factory Recommendation.fromJson(Map<String, dynamic> json) {
  return Recommendation(
    itemId: json['item_id']?.toString() ?? '0',
    name: json['name'] ?? 'Unknown',
    // Check if your backend uses 'category' or 'category_name'
    category: json['category'] ?? json['category_name'] ?? 'General', 
    price: (json['price'] as num?)?.toDouble() ?? 0.0,
    imageUrl: json['image_url'],
  );
}
}