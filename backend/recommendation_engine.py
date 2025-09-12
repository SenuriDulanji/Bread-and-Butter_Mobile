"""
Menu Recommendation Engine
Using collaborative filtering and content-based filtering approaches
Inspired by Meta's recommendation systems
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from collections import defaultdict, Counter
import json
from datetime import datetime, timedelta
import random

class MenuRecommendationEngine:
    def __init__(self):
        self.user_item_matrix = None
        self.item_features = None
        self.svd_model = None
        self.user_profiles = {}
        
    def create_user_item_matrix(self, orders_data, menu_items):
        """
        Create user-item interaction matrix from order history
        Similar to Meta's approach for user-item interactions
        """
        user_items = defaultdict(lambda: defaultdict(int))
        
        # Build interaction matrix from order history
        for order in orders_data:
            user_id = order['user_id']
            items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
            
            for item in items:
                item_id = item.get('item_id') or item.get('id')
                quantity = item.get('quantity', 1)
                if item_id:
                    user_items[user_id][item_id] += quantity
        
        # Convert to DataFrame
        all_users = list(user_items.keys())
        all_items = set()
        for user_dict in user_items.values():
            all_items.update(user_dict.keys())
        all_items = list(all_items)
        
        # Create matrix
        matrix_data = []
        for user_id in all_users:
            row = []
            for item_id in all_items:
                row.append(user_items[user_id].get(item_id, 0))
            matrix_data.append(row)
        
        self.user_item_matrix = pd.DataFrame(matrix_data, index=all_users, columns=all_items)
        return self.user_item_matrix
    
    def extract_item_features(self, menu_items):
        """
        Extract item features for content-based filtering
        Using category, price range, and popularity features
        """
        features = {}
        for item in menu_items:
            item_id = item['id']
            features[item_id] = {
                'category_id': item.get('category_id', 0),
                'price_range': self._get_price_range(item.get('price', 0)),
                'is_available': item.get('is_available', True),
                'discount_percentage': item.get('discount_percentage', 0)
            }
        
        self.item_features = features
        return features
    
    def _get_price_range(self, price):
        """Categorize items by price range"""
        if price < 5:
            return 1  # Low
        elif price < 15:
            return 2  # Medium
        else:
            return 3  # High
    
    def train_collaborative_filtering(self):
        """
        Train collaborative filtering model using SVD
        Similar to Meta's matrix factorization approach
        """
        if self.user_item_matrix is None or self.user_item_matrix.empty:
            return None
        
        # Apply SVD for matrix factorization
        self.svd_model = TruncatedSVD(n_components=min(10, self.user_item_matrix.shape[1] - 1), random_state=42)
        
        # Fit the model on the user-item matrix
        user_item_array = self.user_item_matrix.values
        self.svd_model.fit(user_item_array)
        
        return self.svd_model
    
    def get_user_profile(self, user_id, orders_data):
        """
        Build user profile from order history
        Including category preferences, price preferences, and recency
        """
        user_orders = [order for order in orders_data if order['user_id'] == user_id]
        
        if not user_orders:
            return self._get_default_profile()
        
        category_counts = Counter()
        price_sum = 0
        item_count = 0
        recent_items = set()
        
        # Analyze last 30 days for recency
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for order in user_orders:
            order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
            
            for item in items:
                item_id = item.get('item_id') or item.get('id')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)
                
                # Category preferences
                if 'category_id' in item:
                    category_counts[item['category_id']] += quantity
                
                # Price preferences
                price_sum += price * quantity
                item_count += quantity
                
                # Recent items (for diversity)
                if order_date > thirty_days_ago:
                    recent_items.add(item_id)
        
        profile = {
            'preferred_categories': dict(category_counts.most_common()),
            'avg_price_preference': price_sum / item_count if item_count > 0 else 10,
            'recent_items': list(recent_items),
            'order_frequency': len(user_orders),
            'total_items_ordered': item_count
        }
        
        self.user_profiles[user_id] = profile
        return profile
    
    def _get_default_profile(self):
        """Default profile for new users"""
        return {
            'preferred_categories': {},
            'avg_price_preference': 10,
            'recent_items': [],
            'order_frequency': 0,
            'total_items_ordered': 0
        }
    
    def get_recommendations(self, user_id, orders_data, menu_items, num_recommendations=3):
        """
        Get personalized menu recommendations for a user
        Combines collaborative and content-based filtering
        """
        # Ensure we have required data
        if not menu_items:
            return []
        
        # Get user profile
        user_profile = self.get_user_profile(user_id, orders_data)
        
        # Get available menu items (exclude recently ordered for diversity)
        available_items = [item for item in menu_items if item.get('is_available', True)]
        
        if not available_items:
            return []
        
        # Filter out recently ordered items for diversity (last 7 days)
        recent_items = set(user_profile.get('recent_items', []))
        diverse_items = [item for item in available_items if item['id'] not in recent_items]
        
        # If too few items after filtering, include some recent ones
        if len(diverse_items) < num_recommendations:
            diverse_items = available_items
        
        # Score items based on user preferences
        scored_items = []
        for item in diverse_items:
            score = self._calculate_item_score(item, user_profile)
            scored_items.append((item, score))
        
        # Sort by score and get top recommendations
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # Add some randomness to avoid always showing the same items
        top_items = scored_items[:min(num_recommendations * 2, len(scored_items))]
        
        # Randomly select from top scored items
        if len(top_items) > num_recommendations:
            weights = [score for _, score in top_items]
            selected_indices = np.random.choice(
                len(top_items), 
                size=num_recommendations, 
                replace=False,
                p=np.array(weights) / sum(weights)
            )
            recommendations = [top_items[i][0] for i in selected_indices]
        else:
            recommendations = [item for item, _ in top_items]
        
        return recommendations[:num_recommendations]
    
    def _calculate_item_score(self, item, user_profile):
        """
        Calculate recommendation score for an item based on user profile
        Uses multiple factors like category preference, price preference, etc.
        """
        score = 0.0
        
        # Category preference score (40% weight)
        category_id = item.get('category_id')
        if category_id in user_profile['preferred_categories']:
            category_freq = user_profile['preferred_categories'][category_id]
            total_orders = user_profile['total_items_ordered']
            category_preference = category_freq / total_orders if total_orders > 0 else 0
            score += category_preference * 0.4
        
        # Price preference score (25% weight)
        item_price = item.get('price', 0)
        user_avg_price = user_profile['avg_price_preference']
        
        # Prefer items close to user's average price preference
        price_diff = abs(item_price - user_avg_price)
        max_price = max(item_price, user_avg_price, 1)
        price_similarity = 1 - (price_diff / max_price)
        score += price_similarity * 0.25
        
        # Discount preference (15% weight)
        discount = item.get('discount_percentage', 0)
        if discount > 0:
            score += (discount / 100) * 0.15
        
        # Popularity boost (10% weight) - items with higher original prices tend to be premium
        price_boost = min(item_price / 20, 1.0)  # Normalize to 0-1
        score += price_boost * 0.1
        
        # Randomness for exploration (10% weight)
        score += random.random() * 0.1
        
        return score
    
    def get_trending_items(self, orders_data, menu_items, days=7, limit=3):
        """
        Get trending items based on recent order frequency
        Fallback for users with no order history
        """
        if not orders_data or not menu_items:
            return random.sample(menu_items, min(limit, len(menu_items)))
        
        # Count item frequency in recent orders
        cutoff_date = datetime.now() - timedelta(days=days)
        item_counts = Counter()
        
        for order in orders_data:
            try:
                order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                if order_date > cutoff_date:
                    items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                    for item in items:
                        item_id = item.get('item_id') or item.get('id')
                        if item_id:
                            item_counts[item_id] += item.get('quantity', 1)
            except:
                continue
        
        # Get trending items
        trending_item_ids = [item_id for item_id, _ in item_counts.most_common(limit)]
        trending_items = []
        
        available_items = [item for item in menu_items if item.get('is_available', True)]
        
        for item in available_items:
            if item['id'] in trending_item_ids:
                trending_items.append(item)
        
        # Fill with random items if not enough trending items
        while len(trending_items) < limit and len(trending_items) < len(available_items):
            remaining_items = [item for item in available_items if item not in trending_items]
            if remaining_items:
                trending_items.append(random.choice(remaining_items))
            else:
                break
        
        return trending_items[:limit]

# Global recommendation engine instance
recommendation_engine = MenuRecommendationEngine()