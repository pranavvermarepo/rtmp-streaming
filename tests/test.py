import sys
import time
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from processor import StreamProcessor

def test_stream_processor():
    """
    Test the functionality of the StreamProcessor class.
    """
    video_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'video1.mp4')
    # Test Input URL
    input_url = video_path  # Replace with video file path or rtmp live stream url.

    # Create an instance of StreamProcessor
    processor = StreamProcessor(output_dir="test_output")
    
    # Start stream processing
    try:
        print("Starting stream processing...")
        output_path = processor.start_stream(input_url)

        # Check if output directory exists
        if os.path.exists(output_path):
            print(f"Output directory created: {output_path}")
        else:
            print("Error: Output directory not created.")

        # Test monitoring health
        print("Monitoring stream health...")
        health = processor.monitor_health()
        print("Health metrics:", health)

        # Simulate waiting for the transcoding to complete (adjust based on actual transcoding time)
        time.sleep(5)  # Sleep for 5 seconds as a placeholder for transcoding time
        #
        # Test final health metrics after completion
        final_health = processor.monitor_health()
        print("Final health metrics:", final_health)
    
    except Exception as e:
        print(f"An error occurred during stream processing: {e}")
    
    # Clean up (optional)
    print("Test completed.")

if __name__ == "__main__":
    test_stream_processor()
