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
        # Step 1: Download the entire video using yt-dlp (Prevents ffmpeg 403 network errors)
        # Step 1: Download the entire video using yt-dlp (Spoofing Android client to bypass 403s)
        download_cmd = [
            "yt-dlp",
            "--cookies", "cookies.txt",
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "--extractor-args", "youtube:player_client=android",
            "-o", f"full_{filename}",
            url
        ]
        subprocess.run(download_cmd, check=True)

        # Step 2: Use FFmpeg offline to Trim and Crop the local file
        if ratio == "9:16":
            # Trim the times and Crop the center for Shorts/Reels
            ffmpeg_cmd = [
                "ffmpeg", "-i", f"full_{filename}",
                "-ss", start_time, "-to", end_time,
                "-vf", "crop=ih*(9/16):ih", 
                "-c:a", "copy",
                filename
            ]
        else:
            # Just Trim the times for 16:9
            ffmpeg_cmd = [
                "ffmpeg", "-i", f"full_{filename}",
                "-ss", start_time, "-to", end_time,
                "-c:v", "copy", "-c:a", "copy",
                filename
            ]

        subprocess.run(ffmpeg_cmd, check=True)

        # Step 3: Send the final clipped file to user
        response = send_file(filename, as_attachment=True)
        return response

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Failed to process video. Check server logs."}), 500
    finally:
        # Cleanup ALL server storage so Render doesn't run out of free space
        if os.path.exists(f"full_{filename}"): os.remove(f"full_{filename}")
        if os.path.exists(filename): os.remove(filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
