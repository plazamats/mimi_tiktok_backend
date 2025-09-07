from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import os
import ssl
from dotenv import load_dotenv
from datetime import datetime
import urllib.parse

load_dotenv()

class MongoDB:
    def __init__(self):
        # Get connection string from environment variable
        connection_string = os.getenv('MONGODB_URI')
        if not connection_string:
            raise ValueError("MONGODB_URI environment variable is required")
        
        # Create MongoClient with SSL configuration for Render
        self.client = MongoClient(
            connection_string,
            server_api=ServerApi('1'),  # Stable API version
            # SSL configuration for Render compatibility
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsInsecure=False,
            # Recommended settings for production
            maxPoolSize=50,
            minPoolSize=10,
            connectTimeoutMS=30000,
            socketTimeoutMS=45000,
            serverSelectionTimeoutMS=30000,
            retryWrites=True,
            appname="mimi-tiktok-backend"
        )
        
        # Test the connection with the new ping command
        try:
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB!")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            # Fallback to mock data mode
            self.db = None
            self.reels = None
            print("⚠️  Running in mock data mode - no database connection")
            return
        
        self.db = self.client.mimi_tiktok
        self.reels = self.db.reels
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for better performance"""
        if not self.reels:
            return
            
        try:
            # Index for sorting by creation date
            self.reels.create_index([("created_at", -1)])
            
            # Index for user-specific queries
            self.reels.create_index([("author.username", 1)])
            
            # Index for hashtag searches
            self.reels.create_index([("hashtags", 1)])
            
            # Text index for search functionality
            self.reels.create_index([
                ("description", "text"),
                ("author.username", "text"),
                ("hashtags", "text")
            ])
            
            print("✅ Database indexes created successfully!")
        except Exception as e:
            print(f"⚠️  Could not create indexes: {e}")
    
    def save_reel(self, reel_data):
        """Save a reel to the database"""
        if not self.reels:
            return "mock_id_" + str(os.urandom(4).hex())
            
        try:
            # Add timestamps
            reel_data['created_at'] = datetime.now()
            reel_data['updated_at'] = datetime.now()
            
            # Insert the document
            result = self.reels.insert_one(reel_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving reel: {e}")
            return "mock_id_" + str(os.urandom(4).hex())
    
    def get_reels(self, limit=20, skip=0, hashtag=None, username=None):
        """Get reels with optional filtering"""
        if not self.reels:
            # Return mock data if no database connection
            from tiktok_service import TikTokService
            tiktok_service = TikTokService()
            return tiktok_service.get_trending_videos(limit)
            
        try:
            # Build query based on filters
            query = {}
            if hashtag:
                query['hashtags'] = {'$in': [hashtag.lower()]}
            if username:
                query['author.username'] = username.lower()
            
            reels = list(self.reels.find(query)
                .sort('created_at', -1)
                .skip(skip)
                .limit(limit))
            
            # Convert for JSON response
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
            # Fallback to mock data
            from tiktok_service import TikTokService
            tiktok_service = TikTokService()
            return tiktok_service.get_trending_videos(limit)
    
    # ... [keep the rest of your methods with similar fallback handling] ...

    def get_reel_stats(self):
        """Get overall statistics about reels"""
        if not self.reels:
            return {'total_reels': 0, 'total_likes': 0, 'avg_likes_per_reel': 0}
            
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