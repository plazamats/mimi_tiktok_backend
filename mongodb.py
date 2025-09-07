from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import os
import ssl
from dotenv import load_dotenv
from datetime import datetime
import certifi

load_dotenv()

class MongoDB:
    def __init__(self):
        # Get connection string from environment variable
        connection_string = os.getenv('MONGODB_URI')
        if not connection_string:
            print("⚠️  MONGODB_URI not set, using mock data mode")
            self.client = None
            self.db = None
            self.reels = None
            return
        
        try:
            # Create MongoClient with proper SSL configuration for Render
            self.client = MongoClient(
                connection_string,
                server_api=ServerApi('1'),
                # CRITICAL: Add these SSL parameters for Render
                tls=True,
                tlsCAFile=certifi.where(),  # Use certifi's CA bundle
                tlsAllowInvalidCertificates=False,
                # Connection settings
                maxPoolSize=50,
                minPoolSize=10,
                connectTimeoutMS=30000,
                socketTimeoutMS=45000,
                serverSelectionTimeoutMS=30000,
                retryWrites=True,
                appname="mimi-tiktok-backend"
            )
            
            # Test the connection
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB with SSL!")
            
            self.db = self.client.mimi_tiktok
            self.reels = self.db.reels
            self._create_indexes()
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("⚠️  Falling back to mock data mode")
            self.client = None
            self.db = None
            self.reels = None
    
    def _create_indexes(self):
        """Create necessary indexes for better performance"""
        if not self.reels:
            return
            
        try:
            self.reels.create_index([("created_at", -1)])
            self.reels.create_index([("author.username", 1)])
            self.reels.create_index([("hashtags", 1)])
            self.reels.create_index([
                ("description", "text"),
                ("author.username", "text"),
                ("hashtags", "text")
            ])
            print("✅ Database indexes created successfully!")
        except Exception as e:
            print(f"⚠️  Could not create indexes: {e}")
    
    def is_connected(self):
        return self.client is not None

    def save_reel(self, reel_data):
        if not self.is_connected():
            return "mock_id_" + str(os.urandom(4).hex())
            
        try:
            reel_data['created_at'] = datetime.now()
            reel_data['updated_at'] = datetime.now()
            result = self.reels.insert_one(reel_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving reel: {e}")
            return "mock_id_" + str(os.urandom(4).hex())
    
    def get_reels(self, limit=20, skip=0, hashtag=None, username=None):
        if not self.is_connected():
            from tiktok_service import TikTokService
            return TikTokService().get_trending_videos(limit)
            
        try:
            query = {}
            if hashtag:
                query['hashtags'] = {'$in': [hashtag.lower()]}
            if username:
                query['author.username'] = username.lower()
            
            reels = list(self.reels.find(query)
                .sort('created_at', -1)
                .skip(skip)
                .limit(limit))
            
            processed_reels = []
            for reel in reels:
                processed_reel = {
                    'id': str(reel['_id']),
                    'videoUrl': reel.get('videoUrl', ''),
                    'thumbnailUrl': reel.get('thumbnailUrl', ''),
                    'description': reel.get('description', ''),
                    'author': reel.get('author', {}),
                    'stats': reel.get('stats', {}),
                    'duration': reel.get('duration', 0),
                    'hashtags': reel.get('hashtags', []),
                    'likes': reel.get('likes', []),
                    'comments': reel.get('comments', []),
                    'createdAt': reel.get('created_at').isoformat() if reel.get('created_at') else None,
                    'isMock': reel.get('isMock', False)
                }
                processed_reels.append(processed_reel)
            
            return processed_reels
            
        except Exception as e:
            print(f"Error getting reels: {e}")
            from tiktok_service import TikTokService
            return TikTokService().get_trending_videos(limit)
    
    def like_reel(self, reel_id, user_id):
        if not self.is_connected():
            return True  # Mock success
            
        try:
            result = self.reels.update_one(
                {'_id': ObjectId(reel_id)},
                {
                    '$addToSet': {'likes': user_id},
                    '$set': {'updated_at': datetime.now()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error liking reel: {e}")
            return False
    
    def add_comment(self, reel_id, user_id, comment_text):
        if not self.is_connected():
            return True  # Mock success
            
        try:
            comment_data = {
                'id': str(ObjectId()),
                'user_id': user_id,
                'text': comment_text,
                'timestamp': datetime.now()
            }
            
            result = self.reels.update_one(
                {'_id': ObjectId(reel_id)},
                {
                    '$push': {'comments': comment_data},
                    '$set': {'updated_at': datetime.now()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def search_reels(self, search_term, limit=20):
        if not self.is_connected():
            from tiktok_service import TikTokService
            all_videos = TikTokService().get_trending_videos(50)
            return [v for v in all_videos if search_term.lower() in v.get('description', '').lower()][:limit]
            
        try:
            reels = list(self.reels.find(
                {'$text': {'$search': search_term}},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})])
            .limit(limit))
            
            processed_reels = []
            for reel in reels:
                processed_reel = {
                    'id': str(reel['_id']),
                    'videoUrl': reel.get('videoUrl', ''),
                    'thumbnailUrl': reel.get('thumbnailUrl', ''),
                    'description': reel.get('description', ''),
                    'author': reel.get('author', {}),
                    'score': reel.get('score', 0)
                }
                processed_reels.append(processed_reel)
            
            return processed_reels
        except Exception as e:
            print(f"Error searching reels: {e}")
            from tiktok_service import TikTokService
            all_videos = TikTokService().get_trending_videos(50)
            return [v for v in all_videos if search_term.lower() in v.get('description', '').lower()][:limit]
    
    def get_reel_stats(self):
        if not self.is_connected():
            return {'total_reels': 0, 'total_likes': 0, 'avg_likes_per_reel': 0, 'mode': 'mock_data'}
            
        try:
            total_reels = self.reels.count_documents({})
            total_likes = self.reels.aggregate([
                {'$project': {'likes_count': {'$size': {'$ifNull': ['$likes', []]}}}},
                {'$group': {'_id': None, 'total': {'$sum': '$likes_count'}}}
            ])
            
            total_likes_count = next(total_likes, {}).get('total', 0)
            
            return {
                'total_reels': total_reels,
                'total_likes': total_likes_count,
                'avg_likes_per_reel': total_likes_count / total_reels if total_reels > 0 else 0
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'total_reels': 0, 'total_likes': 0, 'avg_likes_per_reel': 0}