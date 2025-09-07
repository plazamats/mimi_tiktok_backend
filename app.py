from flask import Flask, jsonify, request
from flask_cors import CORS
from mongodb import MongoDB
from tiktok_service import TikTokService
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize services with error handling
try:
    db = MongoDB()
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("⚠️  Running in mock data mode")
    db = None  # Will use mock data from TikTokService

tiktok_service = TikTokService()

@app.route('/')
def home():
    database_status = "connected" if db and db.client else "disconnected (using mock data)"
    return jsonify({
        "message": "Mimi TikTok Reels API", 
        "status": "active",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": f"MongoDB {database_status}",
        "note": "Using mock TikTok data if database unavailable"
    })

@app.route('/health')
def health_check():
    if db:
        stats = db.get_reel_stats()
    else:
        stats = {"total_reels": 0, "total_likes": 0, "avg_likes_per_reel": 0, "mode": "mock_data"}
    
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "database_connected": db is not None,
        "database_stats": stats
    })

@app.route('/tiktok/trending')
def get_trending_videos():
    try:
        count = int(request.args.get('count', 20))
        videos = tiktok_service.get_trending_videos(count)
        return jsonify({
            "success": True,
            "videos": videos,
            "count": len(videos),
            "source": "mock_data" if db is None else "database"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tiktok/hashtag/<hashtag>')
def get_hashtag_videos(hashtag):
    try:
        count = int(request.args.get('count', 20))
        videos = tiktok_service.get_videos_by_hashtag(hashtag, count)
        return jsonify({
            "success": True,
            "hashtag": hashtag,
            "videos": videos,
            "count": len(videos),
            "source": "mock_data" if db is None else "database"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tiktok/user/<username>')
def get_user_videos(username):
    try:
        count = int(request.args.get('count', 20))
        videos = tiktok_service.get_user_videos(username, count)
        return jsonify({
            "success": True,
            "username": username,
            "videos": videos,
            "count": len(videos),
            "source": "mock_data" if db is None else "database"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reels/save', methods=['POST'])
def save_reel():
    try:
        reel_data = request.get_json()
        if not reel_data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        if db:
            reel_id = db.save_reel(reel_data)
            return jsonify({"success": True, "id": reel_id, "saved_to": "database"})
        else:
            return jsonify({"success": True, "id": "mock_id", "saved_to": "mock_data", "note": "Database not connected"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reels')
def get_reels():
    try:
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        hashtag = request.args.get('hashtag')
        username = request.args.get('username')
        
        if db:
            reels = db.get_reels(limit, skip, hashtag, username)
            source = "database"
        else:
            reels = tiktok_service.get_trending_videos(limit)
            source = "mock_data"
            
        return jsonify({
            "success": True,
            "reels": reels,
            "count": len(reels),
            "source": source
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reels/<reel_id>/like', methods=['POST'])
def like_reel(reel_id):
    try:
        user_data = request.get_json()
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return jsonify({"success": False, "error": "User ID required"}), 400
            
        if db:
            success = db.like_reel(reel_id, user_id)
            return jsonify({"success": success, "action": "liked", "saved_to": "database"})
        else:
            return jsonify({"success": True, "action": "liked", "saved_to": "mock_data", "note": "Database not connected"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reels/<reel_id>/comment', methods=['POST'])
def add_comment(reel_id):
    try:
        comment_data = request.get_json()
        user_id = comment_data.get('user_id') if comment_data else None
        comment = comment_data.get('comment') if comment_data else None
        
        if not user_id or not comment:
            return jsonify({"success": False, "error": "User ID and comment required"}), 400
            
        if db:
            success = db.add_comment(reel_id, user_id, comment)
            return jsonify({"success": success, "action": "commented", "saved_to": "database"})
        else:
            return jsonify({"success": True, "action": "commented", "saved_to": "mock_data", "note": "Database not connected"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reels/search')
def search_reels():
    try:
        search_term = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))
        
        if not search_term:
            return jsonify({"success": False, "error": "Search term required"}), 400
            
        if db:
            reels = db.search_reels(search_term, limit)
            source = "database"
        else:
            # Fallback to mock search - filter trending videos by search term
            all_videos = tiktok_service.get_trending_videos(50)
            reels = [v for v in all_videos if search_term.lower() in v.get('description', '').lower()]
            reels = reels[:limit]
            source = "mock_data"
            
        return jsonify({
            "success": True, 
            "reels": reels, 
            "count": len(reels),
            "source": source
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stats')
def get_stats():
    try:
        if db:
            stats = db.get_reel_stats()
            source = "database"
        else:
            stats = {
                "total_reels": 0,
                "total_likes": 0, 
                "avg_likes_per_reel": 0,
                "mode": "mock_data"
            }
            source = "mock_data"
            
        return jsonify({
            "success": True, 
            "stats": stats,
            "source": source
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')