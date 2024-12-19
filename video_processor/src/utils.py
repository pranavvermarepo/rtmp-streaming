import os

import re

def is_url(input_url: str) -> bool:
    """
    Check if the provided input is a valid URL (including HTTP, HTTPS, RTSP, RTMP, etc.).
    """
    url_pattern = re.compile(r'^(?:https?|rtsp?|rtmp)://(?:[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-zA-Z0-9()]{1,6}\b|localhost|[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})[:0-9]*[-a-zA-Z0-9@:%_\+.~#?&//=]*$', re.IGNORECASE)
    return bool(url_pattern.match(input_url))


def validate_input(input_url: str) -> None:
    """
    Validate the input video URL or local file path.
    """
    if not input_url:
        raise ValueError("Input URL cannot be empty.")
    
    if is_url(input_url):
        # For URLs, just check if the format is valid
        pass
    else:
        # For local files, ensure they exist
        if not os.path.isfile(input_url):
            raise FileNotFoundError(f"File not found: {input_url}")

def generate_manifest_links(stream_path: str) -> dict:
    """
    Generate links to HLS manifests for 720p and 480p streams.
    """
    return {
        "720p": os.path.join(stream_path, "720p.m3u8"),
        "480p": os.path.join(stream_path, "480p.m3u8"),
        "1080p": os.path.join(stream_path, "1080p.m3u8")
    }
