from flask import Flask, jsonify, request
from flask_cors import CORS
from mongodb import MongoDB
from tiktok_service import TikTokService
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize services
db = MongoDB()
tiktok_service = TikTokService()

@app.route('/')
def home():
    return jsonify({
        "message": "Mimi TikTok Reels API", 
        "status": "active",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": "MongoDB with PyMongo 4.7.0+"
    })

@app.route('/health')
def health_check():
    stats = db.get_reel_stats()
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "database_stats": stats
    })

# ... [keep all your existing endpoints] ...

@app.route('/reels/search')
def search_reels():
    try:
        search_term = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))
        
        if not search_term:
            return jsonify({"success": False, "error": "Search term required"}), 400
            
        reels = db.search_reels(search_term, limit)
        return jsonify({"success": True, "reels": reels, "count": len(reels)})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stats')
def get_stats():
    try:
        stats = db.get_reel_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')