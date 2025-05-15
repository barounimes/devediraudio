import os
import tempfile
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Carpeta donde se guardarán los segmentos de audio
SEGMENTS_FOLDER = "/tmp/segments"
os.makedirs(SEGMENTS_FOLDER, exist_ok=True)

# Limpiar la carpeta de segmentos antes de cada división
def limpiar_segmentos():
    for f in os.listdir(SEGMENTS_FOLDER):
        if f.startswith("segment_") and f.endswith(".mp3"):
            os.remove(os.path.join(SEGMENTS_FOLDER, f))

@app.route("/split", methods=["POST"])
def split_audio():
    audio_file = request.files.get("file")
    if not audio_file:
        return jsonify({"error": "Falta el archivo"}), 400

    # Limpiar archivos anteriores
    limpiar_segmentos()

    # Guardar archivo de entrada
    input_path = os.path.join(SEGMENTS_FOLDER, secure_filename("input.mp3"))
    audio_file.save(input_path)

    # Patrón de salida para los fragmentos
    output_pattern = os.path.join(SEGMENTS_FOLDER, "segment_%03d.mp3")

    try:
        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-f", "segment", "-segment_time", "30",
            "-c", "copy", output_pattern
        ], check=True)

        # Listar fragmentos y generar URLs
        segments = sorted([
            f for f in os.listdir(SEGMENTS_FOLDER)
            if f.startswith("segment_") and f.endswith(".mp3")
        ])

        segment_urls = [
            f"https://{request.host}/segment/{f}" for f in segments
        ]

        return jsonify({"segments": segment_urls})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error al dividir el audio", "details": str(e)}), 500

@app.route("/segment/<filename>")
def serve_segment(filename):
    return send_from_directory(SEGMENTS_FOLDER, filename, mimetype="audio/mpeg")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "segments": os.listdir(SEGMENTS_FOLDER)})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
