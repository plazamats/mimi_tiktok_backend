import requests
import random

class TikTokService:
    def get_trending_videos(self, count=20):
        """Get mock trending TikTok videos"""
        return self._generate_mock_videos(count, "trending")
    
    def get_videos_by_hashtag(self, hashtag, count=20):
        """Get mock videos by hashtag"""
        return self._generate_mock_videos(count, hashtag)
    
    def get_user_videos(self, username, count=20):
        """Get mock user videos"""
        return self._generate_mock_videos(count, username)
    
    def _generate_mock_videos(self, count, context):
        videos = []
        for i in range(count):
            video_id = f"video_{context}_{i}_{random.randint(1000, 9999)}"
            
            # Use real sample video URLs that work
            sample_videos = [
                "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
                "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_2mb.mp4",
                "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
            ]
            
            videos.append({
                'id': video_id,
                'videoUrl': random.choice(sample_videos),
                'thumbnailUrl': f"https://picsum.photos/400/700?random={i}",
                'description': f"Awesome {context} video #{i} 🎥",
                'author': {
                    'username': f"user{random.randint(1, 100)}",
                    'nickname': f"User {random.randint(1, 100)}",
                    'avatar': f"https://i.pravatar.cc/150?img={random.randint(1, 70)}"
                },
                'stats': {
                    'likes': random.randint(1000, 100000),
                    'comments': random.randint(50, 5000),
                    'shares': random.randint(20, 2000),
                    'views': random.randint(10000, 1000000)
                },
                'duration': random.randint(15, 60),
                'hashtags': [f'#{context}', '#viral', '#fyp', '#trending'],
                'isMock': True,
                'createdAt': f"2024-01-{random.randint(10, 30)}T{random.randint(10, 23)}:{random.randint(10, 59)}:00Z"
            })
        return videos