import os
import time
import subprocess

def capture_screenshot(output_folder):
    # Ace Stream content ID
    content_id = "1205151f6fa5d95c0eeb543cbce43ccfa6a1b216"
    
    # Start playback in the container (using full path to acestreamengine)
    stream_command = f"docker exec acestream /opt/acestream/acestreamengine --client-console --play-and-exit {content_id}"
    process = subprocess.Popen(stream_command, shell=True)
    
    # Wait for stream to be available
    time.sleep(15)
    
    # Capture screenshot using ffmpeg
    screenshot_command = f"ffmpeg -y -i http://127.0.0.1:6878/ace/getstream -vframes 1 {output_folder}/screenshot.png"
    try:
        subprocess.run(screenshot_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to capture screenshot: {e}")
    
    # Stop the process
    process.terminate()

if __name__ == "__main__":
    # Define output folder
    output_folder = "ace_kanalak"
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Capture screenshot
    capture_screenshot(output_folder)
