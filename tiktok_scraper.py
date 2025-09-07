import requests
import json
import random
import re
from typing import List, Dict, Optional

class TikTokScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_video_data_from_html(self, html: str) -> List[Dict]:
        """Extract video data from TikTok HTML page"""
        videos = []
        
        # Try to find SIGI_STATE data
        sigi_pattern = r'<script id="SIGI_STATE" type="application/json">(.*?)</script>'
        sigi_match = re.search(sigi_pattern, html, re.DOTALL)
        
        if sigi_match:
            try:
                sigi_data = json.loads(sigi_match.group(1))
                item_module = sigi_data.get('ItemModule', {})
                
                for video_id, video_data in item_module.items():
                    try:
                        video = self._process_video_data(video_data)
                        if video:
                            videos.append(video)
                    except Exception as e:
                        print(f"Error processing video {video_id}: {e}")
                        continue
                        
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
        
        return videos
    
    def _process_video_data(self, video_data: Dict) -> Optional[Dict]:
        """Process individual video data"""
        try:
            # Get the best available video URL
            video_url = self._get_video_url(video_data)
            if not video_url:
                return None
            
            return {
                'id': video_data.get('id', f"video_{random.randint(10000, 99999)}"),
                'videoUrl': video_url,
                'thumbnailUrl': video_data.get('video', {}).get('cover', '') or 
                              video_data.get('author', {}).get('avatarThumb', ''),
                'description': video_data.get('desc', 'TikTok Video'),
                'author': {
                    'username': video_data.get('author', {}).get('uniqueId', 'tiktok_user'),
                    'nickname': video_data.get('author', {}).get('nickname', 'TikTok User'),
                    'avatar': video_data.get('author', {}).get('avatarThumb', 'https://i.pravatar.cc/150')
                },
                'stats': {
                    'likes': video_data.get('stats', {}).get('diggCount', random.randint(1000, 100000)),
                    'comments': video_data.get('stats', {}).get('commentCount', random.randint(50, 5000)),
                    'shares': video_data.get('stats', {}).get('shareCount', random.randint(20, 2000)),
                    'views': video_data.get('stats', {}).get('playCount', random.randint(10000, 1000000))
                },
                'duration': video_data.get('video', {}).get('duration', random.randint(15, 60)),
                'hashtags': [challenge['title'] for challenge in video_data.get('challenges', [])][:3],
                'isMock': False,
                'createdAt': video_data.get('createTime', '2024-01-01T00:00:00Z')
            }
            
        except Exception as e:
            print(f"Error in _process_video_data: {e}")
            return None
    
    def _get_video_url(self, video_data: Dict) -> Optional[str]:
        """Extract the best available video URL"""
        # Try multiple possible URL locations
        possible_urls = [
            video_data.get('video', {}).get('downloadAddr'),
            video_data.get('video', {}).get('playAddr'),
            video_data.get('videoUrl'),
            video_data.get('video', {}).get('url'),
        ]
        
        # Filter out invalid URLs
        valid_urls = [url for url in possible_urls if url and isinstance(url, str) and url.startswith('http')]
        
        if valid_urls:
            return valid_urls[0]
        
        # If no URL found, return None (will be filtered out)
        return None
    
    def get_trending_videos(self, count: int = 20) -> List[Dict]:
        """Get trending videos by scraping TikTok website"""
        try:
            # Try to fetch trending page
            url = "https://www.tiktok.com/trending"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                videos = self.extract_video_data_from_html(response.text)
                if videos:
                    return videos[:count]
            
            # If scraping fails, use API fallback
            return self._get_api_trending_videos(count)
            
        except Exception as e:
            print(f"❌ Trending scrape failed: {e}")
            return self._generate_fallback_videos(count, "trending")
    
    def _get_api_trending_videos(self, count: int) -> List[Dict]:
        """Fallback to API endpoint"""
        try:
            url = "https://www.tiktok.com/api/recommend/item_list/"
            params = {
                'aid': '1988',
                'count': count,
                'secUid': '',
                'cursor': '0'
            }
            
            headers = {
                **self.session.headers,
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://www.tiktok.com/',
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('itemList'):
                    return self._process_api_videos(data['itemList'])[:count]
            
            return self._generate_fallback_videos(count, "trending")
            
        except Exception as e:
            print(f"❌ API trending failed: {e}")
            return self._generate_fallback_videos(count, "trending")
    
    def _process_api_videos(self, video_list: List[Dict]) -> List[Dict]:
        """Process API response videos"""
        processed = []
        for video in video_list:
            processed_video = self._process_video_data(video)
            if processed_video:
                processed.append(processed_video)
        return processed
    
    def _generate_fallback_videos(self, count: int, context: str) -> List[Dict]:
        """Generate fallback videos when all else fails"""
        videos = []
        reliable_videos = [
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
        ]
        
        for i in range(count):
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