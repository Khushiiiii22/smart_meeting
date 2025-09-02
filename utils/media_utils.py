import subprocess
import os

def split_media_file(input_path, chunk_length_sec=300, output_dir='uploads/chunks'):
    """
    Split input audio/video file into smaller chunks of specified seconds.
    Returns list of output chunk file paths.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_pattern = os.path.join(output_dir, "chunk_%03d.mp4")  # Change extension if audio only

    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-f", "segment",
        "-segment_time", str(chunk_length_sec),
        "-c", "copy",
        output_pattern
    ]

    subprocess.run(cmd, check=True)

    # Collect chunk file paths sorted
    chunk_files = sorted([
        os.path.join(output_dir, f) for f in os.listdir(output_dir)
        if f.startswith("chunk_")
    ])

    return chunk_files
