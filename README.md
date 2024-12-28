# Video Processor Service

## Overview
This project processes video streams using FFmpeg to generate HLS outputs for Video-on-Demand streaming.

## Features
- Transcodes input video to multiple resolutions (1080p,720p, 480p) using ffmpeg
- Generates HLS manifests (.m3u8) and segments
- Extracts video metadata (resolution, codec, bitrate)
- Monitors stream health

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/video-processor-service.git
   ```
2. Navigate to the project directory:
   ```bash
   cd video-processor-service/src
   ```
3. Install dependencies:
   ```bash
   pip3 install "fastapi[standard]"
   ```
4. Install ffmpeg (if not already installed):
   To ensure ffmpeg is installed, follow these instructions based on your operating system:
   For Ubuntu / Debian-based systems:

   ```bash
      sudo apt update
      sudo apt install ffmpeg
   ```
5. Verify the installation:
   After installation, you can verify that ffmpeg is correctly installed by running the following command in the terminal:

   ```bash
   ffmpeg -version
   ```

## Usage
1. Run the server:
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8001
   ```
2. Access the API documentation at `http://127.0.0.1:8001/docs`.

3. from tests folder using test.py we can test each functionality of class StreamProcessor 

## API Endpoints

### POST /stream/start - Begin stream ingestion
**Description:** This endpoint starts processing a video stream. You can provide either a recorded video file or an RTMP live stream URL as the input.it generates a unique stream id , saves manifest files in output folder and saves logs file.

**Endpoint:**
```
http://127.0.0.1:8001/stream/start

curl command:

curl -X POST 'http://127.0.0.1:8001/stream/start' -H 'Content-Type: application/json' -d '{"input_url":"video1.mp4"}'
```

**Payload:**
```json
{
   "input_url": "rtmp://your-stream-url" or "recorded video_path"
}
```

**Response:**
```json
{
   "message": "Stream processing started",
   "stream_id": "77d3711d-1f7e-4ab8-937c-e6d582721c45",
   "manifests": {
      "720p": "output/77d3711d-1f7e-4ab8-937c-e6d582721c45/720p.m3u8",
      "480p": "output/77d3711d-1f7e-4ab8-937c-e6d582721c45/480p.m3u8",
      "1080p": "output/77d3711d-1f7e-4ab8-937c-e6d582721c45/1080p.m3u8"
   }
}
```

### GET /stream/{stream_id} - Get stream manifest
**Description:** Retrieve the HLS manifests for a specific stream using stream id identifier as input.

**Endpoint:**
```
http://127.0.0.1:8001/stream/{stream_id}

curl command:

curl -X 'GET' 'http://127.0.0.1:8001/stream/a32375e7-2bcf-4ee7-8e23-7c8a898bcfac'

```

**Response:**
```json
{
   "stream_id": "77d3711d-1f7e-4ab8-937c-e6d582721c45",
   "manifests": {
      "720p": "output/77d3711d-1f7e-4ab8-937c-e6d582721c45/720p.m3u8",
      "480p": "output/77d3711d-1f7e-4ab8-937c-e6d582721c45/480p.m3u8",
      "1080p": "output/77d3711d-1f7e-4ab8-937c-e6d582721c45/1080p.m3u8"
   }
}
```

### GET /metrics/{stream_id} - Get stream health metrics
**Description:** Fetch the metrics and status for a specific stream using stream id identifier as input.

**Endpoint:**
```
http://127.0.0.1:8001/metrics/{stream_id}

curl command:

curl -X 'GET' 'http://127.0.0.1:8001/metrics/a32375e7-2bcf-4ee7-8e23-7c8a898bcfac'
```

**Response:**
```json
{
   "stream_id": "aeae2fe8-c8c7-4b90-9c35-7f5c65a6b362",
   "metrics": {
      "status": "completed",
      "480": {
         "Codec": "h264",
         "Pixel_format": "yuv420p",
         "Height": 480,
         "FPS": "29.97",
         "Bitrate": "788.15 kb/s"
      },
      "720": {
         "Codec": "h264",
         "Pixel_format": "yuv420p",
         "Height": 720,
         "FPS": "29.97",
         "Bitrate": "1548.96 kb/s"
      },
      "1080": {
         "Codec": "h264",
         "Pixel_format": "yuv420p",
         "Height": 1080,
         "FPS": "29.97",
         "Bitrate": "3427.32 kb/s"
      }
   }
}
```


## Testing each functionality using test.py located in tests folder

1. input_url default it is recorded video ,
2. run python test.py , it creates and saves manifest files in test_output folder and prints final health metrics
3. in the place of recorded video ,replace with RTMP live stream for testing live stream .


## For sanity check we can generate video file from output.m3u8 transcoded playlist files
ffmpeg -i /PATH/video_processor/tests/test_output/{stream_id}/480p.m3u8  -c:v copy -c:a aac -strict experimental /PATH/video_processor/tests/output_video61.mp4

## Below is optional and documented for knowledge purpose only. This simply demonstrate how we generated an rtmp stream,
however, for this POC purpose we have shared an alreday generated rtmp stream OR you can yourself created one too

## How to Create an RTMP Live Stream
1. **Create an account on [castr.com](https://castr.com):**
   - Sign up and log in to your account.

2. **Create a new live stream:**
   - Navigate to the Livestream section and create a new stream.
   - Select a region and provide a name for your stream.
   - Choose the "All-in-One Stream" option.

3. **Set up OBS Studio:**
   - Download and install OBS Studio from [obsproject.com](https://obsproject.com).
   - Open OBS Studio and go to `Settings` > `Stream`.
   - Select the streaming platform as Castr.
   - Enter the stream key provided by Castr.

4. **Start streaming:**
   - Add your video source in OBS Studio.
   - Click on `Start Streaming` to begin the live stream.

5. **Stop the stream:**
   - To stop the stream, click on `Stop Streaming` in OBS Studio.

Now you can use the RTMP URL in your API's `input_url` to process live streams.

