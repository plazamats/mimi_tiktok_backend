from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import os
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
        
        # Create MongoClient with Server API version 1
        self.client = MongoClient(
            connection_string,
            server_api=ServerApi('1'),  # Stable API version
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
            raise
        
        self.db = self.client.mimi_tiktok
        self.reels = self.db.reels
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for better performance"""
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
        try:
            # Add timestamps
            reel_data['created_at'] = datetime.now()
            reel_data['updated_at'] = datetime.now()
            
            # Insert the document
            result = self.reels.insert_one(reel_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving reel: {e}")
            raise
    
    def get_reels(self, limit=20, skip=0, hashtag=None, username=None):
        """Get reels with optional filtering"""
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
            return []
    
    def like_reel(self, reel_id, user_id):
        """Like a reel"""
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
        """Add comment to a reel"""
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
        """Search reels by text"""
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
            return []
    
    def get_reel_stats(self):
        """Get overall statistics about reels"""
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