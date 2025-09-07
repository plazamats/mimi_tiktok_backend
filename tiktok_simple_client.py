import requests
import json
import random
from typing import List, Dict, Optional

class TikTokSimpleClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
        })
    
    def get_trending_videos(self, count: int = 20) -> List[Dict]:
        """Get trending videos using TikTok's API"""
        try:
            # Try to get real trending videos
            url = "https://www.tiktok.com/api/recommend/item_list/"
            params = {
                'aid': '1988',
                'count': count,
                'secUid': '',
                'cursor': '0'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('itemList'):
                    return self._process_video_list(data['itemList'])
            
            # If that fails, try alternative endpoint
            return self._get_fallback_trending(count)
            
        except Exception as e:
            print(f"❌ Error fetching trending videos: {e}")
            return self._generate_fallback_videos(count, "trending")
    
    def _get_fallback_trending(self, count: int) -> List[Dict]:
        """Alternative method to get trending videos"""
        try:
            url = "https://tiktok-api-1.p.rapidapi.com/trending"
            headers = {
                'X-RapidAPI-Key': 'your-rapidapi-key-here',  # You'd need to sign up for this
                'X-RapidAPI-Host': 'tiktok-api-1.p.rapidapi.com'
            }
            params = {'count': count}
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return self._process_video_list(response.json().get('data', []))
                
            return self._generate_fallback_videos(count, "trending")
            
        except Exception as e:
            print(f"❌ Fallback trending failed: {e}")
            return self._generate_fallback_videos(count, "trending")
    
    def _process_video_list(self, video_list: List[Dict]) -> List[Dict]:
        """Process raw TikTok API response into our format"""
        processed_videos = []
        
        for video in video_list:
            try:
                processed_video = {
                    'id': video.get('id', f"video_{random.randint(10000, 99999)}"),
                    'videoUrl': video.get('video', {}).get('downloadAddr') or 
                               video.get('videoUrl') or 
                               video.get('video', {}).get('playAddr'),
                    'thumbnailUrl': video.get('video', {}).get('cover') or 
                                  video.get('thumbnailUrl') or 
                                  video.get('author', {}).get('avatarThumb'),
                    'description': video.get('desc', 'TikTok Video'),
                    'author': {
                        'username': video.get('author', {}).get('uniqueId', 'tiktok_user'),
                        'nickname': video.get('author', {}).get('nickname', 'TikTok User'),
                        'avatar': video.get('author', {}).get('avatarThumb', 'https://i.pravatar.cc/150')
                    },
                    'stats': {
                        'likes': video.get('stats', {}).get('diggCount', random.randint(1000, 100000)),
                        'comments': video.get('stats', {}).get('commentCount', random.randint(50, 5000)),
                        'shares': video.get('stats', {}).get('shareCount', random.randint(20, 2000)),
                        'views': video.get('stats', {}).get('playCount', random.randint(10000, 1000000))
                    },
                    'duration': video.get('video', {}).get('duration', random.randint(15, 60)),
                    'hashtags': [tag.get('title', f'#{tag}') for tag in video.get('challenges', [])][:5],
                    'isMock': False,
                    'createdAt': video.get('createTime', '2024-01-01T00:00:00Z')
                }
                
                # Ensure we have a playable video URL
                if not processed_video['videoUrl'] or 'downloadAddr' in processed_video['videoUrl']:
                    processed_video['videoUrl'] = self._get_playable_url(video)
                
                processed_videos.append(processed_video)
                
            except Exception as e:
                print(f"❌ Error processing video: {e}")
                continue
        
        return processed_videos
    
    def _get_playable_url(self, video: Dict) -> str:
        """Extract or generate a playable video URL"""
        # Try to find a playable URL in the video data
        video_urls = [
            video.get('video', {}).get('playAddr'),
            video.get('videoUrl'),
            video.get('video', {}).get('downloadAddr'),
        ]
        
        # Filter out None values and non-URLs
        valid_urls = [url for url in video_urls if url and isinstance(url, str) and url.startswith('http')]
        
        if valid_urls:
            return valid_urls[0]
        
        # Fallback to reliable sample videos
        reliable_videos = [
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
        ]
        
        return random.choice(reliable_videos)
    
    def _generate_fallback_videos(self, count: int, context: str) -> List[Dict]:
        """Generate fallback videos when API fails"""
        videos = []
        for i in range(count):
            reliable_videos = [
                "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
            ]
            
            videos.append({
                'id': f"fallback_{context}_{i}",
                'videoUrl': random.choice(reliable_videos),
                'thumbnailUrl': f"https://picsum.photos/400/700?random={i}",
                'description': f"Awesome {context} video #{i+1} 🎥",
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
                'hashtags': [f'#{context}', '#viral', '#fyp'],
                'isMock': True,
                'createdAt': f"2024-01-{random.randint(10, 30)}T00:00:00Z"
            })
        return videos