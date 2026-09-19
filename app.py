from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import subprocess
import uuid

app = Flask(__name__)
CORS(app) # Allows GitHub Pages to talk to this server

@app.route('/clip', methods=['POST'])
def clip_video():
    data = request.json
    url = data.get('url')
    ratio = data.get('ratio')
    start_time = data.get('start')
    end_time = data.get('end')

    if not all([url, ratio, start_time, end_time]):
        return jsonify({"error": "Missing parameters"}), 400

    filename = f"{uuid.uuid4()}.mp4"
    
    try:
        # Step 1: Download specific segment in 1080p using yt-dlp
        download_cmd = [
            "yt-dlp",
            "--cookies", "cookies.txt",
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "--download-sections", f"*{start_time}-{end_time}",
            "-o", f"raw_{filename}",
            url
        ]
        subprocess.run(download_cmd, check=True)

        # Step 2: Apply FFmpeg formatting (Crop to 9:16 if requested)

        # Step 2: Apply FFmpeg formatting (Crop to 9:16 if requested)
        if ratio == "9:16":
            # Crop the center of the video for Shorts/Reels
            ffmpeg_cmd = [
                "ffmpeg", "-i", f"raw_{filename}",
                "-vf", "crop=ih*(9/16):ih", 
                "-c:a", "copy",
                filename
            ]
        else:
            # Just rename/encode if 16:9
            ffmpeg_cmd = ["ffmpeg", "-i", f"raw_{filename}", "-c", "copy", filename]

        subprocess.run(ffmpeg_cmd, check=True)

        # Step 3: Send file to user
        response = send_file(filename, as_attachment=True)
        return response

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Failed to process video. Check timestamps or URL."}), 500
    finally:
        # Cleanup server storage so it doesn't run out of space
        if os.path.exists(f"raw_{filename}"): os.remove(f"raw_{filename}")
        if os.path.exists(filename): os.remove(filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
