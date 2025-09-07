import os
from TikTokApi import TikTokApi
import asyncio
from dotenv import load_dotenv
import json

load_dotenv()

class TikTokAPIClient:
    _instance = None
    _api = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TikTokAPIClient, cls).__new__(cls)
            cls._instance._initialize_api()
        return cls._instance
    
    def _initialize_api(self):
        """Initialize the TikTok API with proper configuration"""
        try:
            # Initialize TikTok API
            self._api = TikTokApi()
            print("✅ TikTok API initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize TikTok API: {e}")
            self._api = None
    
    async def get_trending_videos(self, count=20):
        """Get real trending TikTok videos"""
        if not self._api:
            return []
            
        try:
            async with self._api:
                videos = []
                async for video in self._api.trending.videos(count=count):
                    video_data = await self._process_video(video)
                    if video_data:
                        videos.append(video_data)
                    if len(videos) >= count:
                        break
                return videos
        except Exception as e:
            print(f"❌ Error fetching trending videos: {e}")
            return []
    
    async def get_videos_by_hashtag(self, hashtag, count=20):
        """Get videos by hashtag"""
        if not self._api:
            return []
            
        try:
            async with self._api:
                videos = []
                hashtag_obj = self._api.hashtag(name=hashtag)
                async for video in hashtag_obj.videos(count=count):
                    video_data = await self._process_video(video)
                    if video_data:
                        videos.append(video_data)
                    if len(videos) >= count:
                        break
                return videos
        except Exception as e:
            print(f"❌ Error fetching hashtag videos: {e}")
            return []
    
    async def get_user_videos(self, username, count=20):
        """Get user videos"""
        if not self._api:
            return []
            
        try:
            async with self._api:
                videos = []
                user = self._api.user(username=username)
                async for video in user.videos(count=count):
                    video_data = await self._process_video(video)
                    if video_data:
                        videos.append(video_data)
                    if len(videos) >= count:
                        break
                return videos
        except Exception as e:
            print(f"❌ Error fetching user videos: {e}")
            return []
    
    async def _process_video(self, video):
        """Process a video object into our format"""
        try:
            # Get video info
            video_info = await video.info()
            
            return {
                'id': video_info.get('id', ''),
                'videoUrl': video_info.get('video', {}).get('downloadAddr', ''),
                'thumbnailUrl': video_info.get('video', {}).get('cover', ''),
                'description': video_info.get('desc', ''),
                'author': {
                    'username': video_info.get('author', {}).get('uniqueId', ''),
                    'nickname': video_info.get('author', {}).get('nickname', ''),
                    'avatar': video_info.get('author', {}).get('avatarThumb', '')
                },
                'stats': {
                    'likes': video_info.get('stats', {}).get('diggCount', 0),
                    'comments': video_info.get('stats', {}).get('commentCount', 0),
                    'shares': video_info.get('stats', {}).get('shareCount', 0),
                    'views': video_info.get('stats', {}).get('playCount', 0)
                },
                'duration': video_info.get('video', {}).get('duration', 0),
                'hashtags': [tag.get('title', '') for tag in video_info.get('challenges', [])],
                'isMock': False,
                'createdAt': video_info.get('createTime', '')
            }
        except Exception as e:
            print(f"❌ Error processing video: {e}")
            return None

# Synchronous wrapper for Flask
class TikTokSyncClient:
    def __init__(self):
        self._async_client = TikTokAPIClient()
    
    def get_trending_videos(self, count=20):
        return asyncio.run(self._async_client.get_trending_videos(count))
    
    def get_videos_by_hashtag(self, hashtag, count=20):
        return asyncio.run(self._async_client.get_videos_by_hashtag(hashtag, count))
    
    def get_user_videos(self, username, count=20):
        return asyncio.run(self._async_client.get_user_videos(username, count))