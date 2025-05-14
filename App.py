import os
import tempfile
import subprocess
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

@app.route('/split', methods=['POST'])
def split_audio():
    audio_file = request.files['file']
    if not audio_file:
        return jsonify({"error": "No file uploaded"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp3")
        audio_file.save(input_path)

        output_pattern = os.path.join(tmpdir, "segment_%03d.mp3")
        command = [
            "ffmpeg", "-i", input_path,
            "-f", "segment", "-segment_time", "30",
            "-c", "copy", output_pattern
        ]

        try:
            subprocess.run(command, check=True)
            segments = [f for f in os.listdir(tmpdir) if f.startswith("segment_")]
            segments.sort()

            # Puedes devolver los blobs o URLs si los subes a un CDN o servidor
            return jsonify({"segments": segments})
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "Failed to split audio", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
