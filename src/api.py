from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from processor import StreamProcessor
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from utils import validate_input, generate_manifest_links
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins or restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

processor = StreamProcessor()


class StreamRequest(BaseModel):
    input_url: str


# Endpoint to start processing a stream
@app.post("/stream/start")
def start_stream(request: StreamRequest):
    try:
        video_path = request.input_url
        validate_input(request.input_url)
        print("transcoding process initiated")
        output_path = processor.start_stream(request.input_url)
        stream_id = processor.stream_id  
        
        manifests = generate_manifest_links(output_path)
        return {
            "message": "Stream processing started",
            "stream_id": stream_id,  
            "manifests": manifests
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream/{stream_id}")
def get_stream_manifest(stream_id: str):
    stream_path = os.path.join("output", stream_id)
    if not os.path.exists(stream_path):
        raise HTTPException(status_code=404, detail="Stream not found")

    manifests = generate_manifest_links(stream_path)
    return {"stream_id": stream_id, "manifests": manifests}

# Endpoint to monitor stream health
@app.get("/metrics/{stream_id}")
def get_stream_metrics(stream_id: str):
    try:
        # Check if the stream is still processing
        if processor.running:
            metrics = processor.monitor_health()  
            return {"stream_id": stream_id, "metrics": metrics}
        
        
        final_metrics = processor.monitor_health()  # Fetch final health metrics
        return {"stream_id": stream_id, "metrics": final_metrics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

