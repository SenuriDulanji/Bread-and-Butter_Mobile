class Recommendation {
  final String itemId;
  final String name;
  final String reason;
  final String? imageUrl;
  final double price; // <--- 1. Add this field

  Recommendation({
    required this.itemId,
    required this.name,
    required this.reason,
    this.imageUrl,
    required this.price,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      itemId: json['item_id'] ?? '',
      name: json['name'] ?? 'Unknown Item',
      reason: json['reason'] ?? 'Recommended for you',
      imageUrl: json['image_url'],
      // 3. Parse the price (handles integers safely)
      price: (json['price'] ?? 0).toDouble(), 
    );
  }
}