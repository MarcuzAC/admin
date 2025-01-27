from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Categories
categories = [
    'Rap Battles',
    'MUBAS Got Talent',
    'Music',
    'Social Weekend Highlights',
    'Live'
]

# Database setup
DATABASE = 'videos.db'

def init_db():
    """Initialize the database."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        thumbnail_path TEXT NOT NULL,
                        category TEXT NOT NULL
                    )''')
        conn.commit()

# Initialize the database
init_db()

# Serve uploaded video and thumbnail files
app.config['VIDEO_FOLDER'] = 'local_videos'
app.config['THUMBNAIL_FOLDER'] = 'thumbnails'

@app.route('/videos/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def uploaded_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)

# Routes
@app.route('/categories', methods=['GET'])
def get_categories():
    """Return the list of video categories."""
    return jsonify({'status': 'success', 'data': {'categories': categories}})

@app.route('/media', methods=['GET'])
def get_media():
    """Fetch all videos from the database."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM videos")
            videos = c.fetchall()

        media_list = [
            {
                'id': video[0],
                'title': video[1],
                'file_path': f"http://localhost:5000/videos/{os.path.basename(video[2])}",
                'thumbnail_path': f"http://localhost:5000/thumbnails/{os.path.basename(video[3])}",
                'category': video[4]
            }
            for video in videos
        ]
        return jsonify({'status': 'success', 'data': {'media': media_list}})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Upload a video file locally and save its metadata in the database."""
    # Validate request
    if 'file' not in request.files or 'thumbnail' not in request.files or 'title' not in request.form or 'category' not in request.form:
        return jsonify({'status': 'error', 'error': 'Missing file, thumbnail, title, or category'}), 400

    video_file = request.files['file']
    thumbnail_file = request.files['thumbnail']
    title = request.form['title']
    category = request.form['category']

    # Ensure the category is valid
    if category not in categories:
        return jsonify({'status': 'error', 'error': f'Invalid category. Available categories: {categories}'}), 400

    # Save video file locally
    os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)
    video_path = os.path.join(app.config['VIDEO_FOLDER'], video_file.filename)
    video_file.save(video_path)

    # Save thumbnail file locally
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)
    thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_file.filename)
    thumbnail_file.save(thumbnail_path)

    try:
        # Save to database
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO videos (title, file_path, thumbnail_path, category) VALUES (?, ?, ?, ?)", 
                      (title, video_path, thumbnail_path, category))
            conn.commit()

        return jsonify({
            'status': 'success',
            'data': {
                'message': 'File and thumbnail uploaded successfully',
                'file_path': video_path,
                'thumbnail_path': thumbnail_path
            }
        }), 200
    except Exception as e:
        # Clean up files in case of error
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
