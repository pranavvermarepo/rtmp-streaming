import subprocess
import os
import uuid
import threading
import re
from collections import deque
import logging
import json
import queue

logging.basicConfig(filename='stream_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StreamProcessor:
    """
    Main stream processing class structure.
    Handles video stream processing, transcoding, manifest generation, and health monitoring.
    """

    def __init__(self, output_dir="output"):
        """
        Initializing the StreamProcessor with a specified output directory and set up necessary variables.
        """
        #self.lock = threading.Lock()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.health_metrics = {"status": "idle"}
        self.log_queue = deque(maxlen=50)
        self.running = False
        self.final_health_metrics = {}
        self.stream_id = None
        logging.info("StreamProcessor initialized.")

    def start_stream(self, input_url: str) -> None:
        """
        Initialize stream processing by extracting metadata and preparing for transcoding.
        """
        self.stream_id = str(uuid.uuid4())  # Unique stream ID
        #pre_metadata = self.get_video_metadata(input_url)
        #print("Pre-transcoding Metadata:", pre_metadata)
        output_path = os.path.join(self.output_dir, self.stream_id)
        os.makedirs(output_path, exist_ok=True)
        logging.info(f"Starting stream processing for {input_url}. Output path: {output_path}")
        
        # Start transcoding into multiple resolutions
        self.generate_variants(input_url, output_path)

        # Generate the HLS manifest after transcoding
        self.create_manifest(output_path)
        return output_path

    def generate_variants(self, input_url: str, output_path: str) -> None:
        """
        Handle transcoding to different qualities (1080p, 720p, 480p).
        """
        # FFmpeg command to generate HLS output with multiple resolutions
        ffmpeg_cmd_1080p = [
            "ffmpeg", 
            "-i", input_url,                  # Input file URL or path
            "-c:v", "libx264",                 # Video codec (use 'libx264' for H.264 encoding)
            "-c:a", "aac",                     # Audio codec (AAC)
            "-vf", "scale=1920:1080",           # Scale video to 1920x1080 resolution
            "-hls_time", "8",                   # Set segment duration (in seconds)
            "-hls_list_size", "5",               #to store most recent 5 segments
            "-hls_flags", "delete_segments",     #to remove degments which are not in index file of .m3u8
            "-hls_playlist_type", "event",       # Set playlist type to Video on Demand
            "-loglevel", "info",               # Set log level to info (less verbose)
            f"{output_path}/1080p.m3u8" 
        ]
        

        ffmpeg_cmd_720p = [
            "ffmpeg", 
            "-i", input_url,                 
            "-c:v", "libx264",                 
            "-c:a", "aac",                     
            "-vf", "scale=1280:720",           
            "-hls_time", "8",   
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments",               
            "-hls_playlist_type", "event",      
            "-loglevel", "info",              
            f"{output_path}/720p.m3u8" 
        ]

        ffmpeg_cmd_480p = [
            "ffmpeg", 
            "-i", input_url,                 
            "-c:v", "libx264",                
            "-c:a", "aac",                     
            "-vf", "scale=854:480",           
            "-hls_time", "8",  
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments",                
            "-hls_playlist_type", "event",      
            "-loglevel", "info",              
            f"{output_path}/480p.m3u8"
        ]

        try:
            self.running = True
            process_1080p = subprocess.Popen(ffmpeg_cmd_1080p, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process_720p = subprocess.Popen(ffmpeg_cmd_720p, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process_480p = subprocess.Popen(ffmpeg_cmd_480p, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor FFmpeg logs for all resolutions
            log_thread_1080p = threading.Thread(target=self._monitor_ffmpeg_logs, args=(process_1080p, "1080"))
            log_thread_720p = threading.Thread(target=self._monitor_ffmpeg_logs, args=(process_720p, "720"))
            log_thread_480p = threading.Thread(target=self._monitor_ffmpeg_logs, args=(process_480p, "480"))
            log_thread_1080p.start()
            log_thread_720p.start()
            log_thread_480p.start()
              
            process_1080p.wait()
            process_720p.wait()
            process_480p.wait() 
            log_thread_1080p.join()   
            log_thread_720p.join() 
            log_thread_480p.join() 
            self.running = False
            self.health_metrics["status"] = "completed"
            self._save_final_metrics()
            if process_1080p.returncode != 0:
                print("FFmpeg error log:")
                #print(stderr)
                raise Exception("FFmpeg process failed.")
            logging.info(f"Stream processing completed. Output directory: {output_path}")
        except Exception as e:
            logging.error(f"Stream processing failed: {e}")
            raise Exception(f"Stream processing failed: {e}")

    def create_manifest(self, output_path: str) -> None:
        """
        Generate HLS manifest by concatenating multiple playlists into a master playlist.
        """
        try:
            master_playlist_path = os.path.join(output_path, "master.m3u8")
            with open(master_playlist_path, "w") as master_playlist:
                master_playlist.write("#EXTM3U\n")
                master_playlist.write("#EXT-X-VERSION:3\n")
                master_playlist.write("#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1920x1080\n")
                master_playlist.write(f"1080p.m3u8\n")
                master_playlist.write("#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=1280x720\n")
                master_playlist.write(f"720p.m3u8\n")
                master_playlist.write("#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=854x480\n")
                master_playlist.write(f"480p.m3u8\n")

            logging.info(f"Master playlist generated: {master_playlist_path}")
        except Exception as e:
            logging.error(f"Failed to generate master playlist: {e}")
            raise Exception(f"Failed to generate master playlist: {e}")

    def get_video_metadata(self, input_url: str) -> dict:
        """
        Extract metadata from the video using FFprobe.
        """
        ffprobe_cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=bit_rate:stream=width,height,r_frame_rate,codec_name",
            "-of", "json", input_url
        ]
        try:
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFprobe failed with error: {result.stderr}")
            metadata = json.loads(result.stdout)
            return metadata
        except Exception as e:
            raise Exception(f"Error extracting metadata: {e}")

    def _monitor_ffmpeg_logs(self, process, resolution_label) -> None:
        """
        Monitor FFmpeg logs for a specific process and resolution.
        """
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if line:
                logging.info(f"[{resolution_label}] Line read from FFmpeg stderr: {line.strip()}")
                self.extract_video_metrics(line, resolution_label)

    def extract_video_metrics(self, line, resolution_label) -> None:
        """
        Extract codec, resolution, and FPS from FFmpeg log lines.
        """
        #print("metrics",self.health_metrics)
        import re
             
        height_g = f"{resolution_label}"
        bitrate=None
        if "Video:" in line:
            
            video_pattern = r"Video:\s*(\S+)\s*\(.*?\),\s*(\S+).*?,\s*(\d+x\d+).*?(\d+(?:\.\d+)?)\s*fps"

            video_match = re.search(video_pattern, line)
            if video_match:
                codec = video_match.group(1) 
                pixel_format = video_match.group(2)  
                cleaned_pixel_format = re.sub(r'\(.*', '', pixel_format).strip()         
                
                fps = video_match.group(4) 
               
                height_g = f"{resolution_label}"
                
                self.health_metrics.setdefault(height_g, {})
                self.health_metrics[height_g]["Codec"] = codec
                
                self.health_metrics[height_g]["Pixel_format"] = cleaned_pixel_format
                self.health_metrics[height_g]["Height"] = resolution_label
                self.health_metrics[height_g]["FPS"] = fps

                print(f"Codec: {codec}")
                print(f"Pixel Format: {cleaned_pixel_format}")
                print(f"Height: {resolution_label}")
                print(f"FPS: {fps}")
                #print("metrics",self.health_metrics)        
        # Extract bitrate
        if "kb/s:" in line:
            bitrate_pattern = r"kb/s:\s*([\d.]+)"
            bitrate_match = re.search(bitrate_pattern, line)

            if bitrate_match:
                bitrate = bitrate_match.group(1)
                #print(f"Extracted bitrate: {bitrate}")
                # Debugging: Check if height_g has been set
                #print(f"height_g before condition: {height_g}")

                # Ensure that height_g is set before trying to store the bitrate
                #if height_g:
                height_g = f"{resolution_label}"
                self.health_metrics[height_g]["Bitrate"] = f"{bitrate} kb/s"
                print(f"Bitrate: {bitrate} kb/s added to {height_g}")
                
                #print("metrics",self.health_metrics)
    def _save_final_metrics(self) -> None:
        """
        Save the final health metrics for post-processing checks.
        """
        self.final_health_metrics = self.health_metrics.copy()
        logging.info(f"Final health metrics saved: {self.final_health_metrics}")

    def monitor_health(self) -> dict:
        """
        Return stream health metrics or final metrics after processing.
        """
        if self.running:
            logging.info(f"Monitoring health: {self.health_metrics}")
            return self.health_metrics
        else:
            logging.info(f"Stream stopped. Final metrics: {self.final_health_metrics}")
            return {"status": "Stream stopped", **self.final_health_metrics}


