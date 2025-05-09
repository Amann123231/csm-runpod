import os
import sys
import base64
import requests
import argparse
import time
from pydub import AudioSegment
from pydub.playback import play
import tempfile

def generate_speech(text, endpoint_id, api_key, speaker=0, max_audio_length_ms=10000):
    """
    Generate speech using CSM-1b on RunPod serverless endpoint
    """
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "text": text,
            "speaker": speaker,
            "max_audio_length_ms": max_audio_length_ms
        }
    }
    
    print(f"Sending request to generate: '{text}'")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    # Get the task ID from the response
    task_id = response.json().get("id")
    if not task_id:
        print("Error: No task ID in response")
        return None
    
    print(f"Task ID: {task_id}")
    
    # Poll for the result
    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{task_id}"
    
    while True:
        time.sleep(2)
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        
        if status_data.get("status") == "COMPLETED":
            print("✅ Generation completed!")
            output = status_data.get("output")
            
            if "error" in output:
                print(f"Error in generation: {output['error']}")
                return None
                
            audio_base64 = output.get("audio_base64")
            sample_rate = output.get("sample_rate")
            duration = output.get("duration_seconds")
            
            print(f"Audio generated: {duration:.2f} seconds at {sample_rate}Hz")
            return audio_base64
            
        elif status_data.get("status") == "FAILED":
            print(f"❌ Generation failed: {status_data.get('error')}")
            return None
            
        else:
            print(f"Status: {status_data.get('status')}. Waiting...")

def save_and_play_audio(audio_base64, output_file=None):
    """
    Save base64 audio to a file and play it
    """
    # Decode the base64 audio
    audio_data = base64.b64decode(audio_base64)
    
    # Save to a temporary file if no output file specified
    if output_file is None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            output_file = temp_file.name
    else:
        with open(output_file, "wb") as f:
            f.write(audio_data)
    
    print(f"Audio saved to {output_file}")
    
    # Play the audio
    audio = AudioSegment.from_file(output_file)
    print("Playing audio...")
    play(audio)
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSM-1b Client for RunPod")
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--endpoint", type=str, help="RunPod endpoint ID")
    parser.add_argument("--api-key", type=str, help="RunPod API key")
    parser.add_argument("--output", type=str, help="Output WAV file path (optional)")
    parser.add_argument("--speaker", type=int, default=0, help="Speaker ID (default: 0)")
    
    args = parser.parse_args()
    
    # Check environment variables if arguments not provided
    text = args.text
    endpoint_id = args.endpoint or os.environ.get("RUNPOD_ENDPOINT_ID")
    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    output_file = args.output
    speaker = args.speaker
    
    if not text:
        text = input("Enter text to convert to speech: ")
    
    if not endpoint_id:
        endpoint_id = input("Enter RunPod endpoint ID: ")
    
    if not api_key:
        api_key = input("Enter RunPod API key: ")
    
    # Generate the speech
    audio_base64 = generate_speech(text, endpoint_id, api_key, speaker)
    
    if audio_base64:
        # Save and play the audio
        save_and_play_audio(audio_base64, output_file) 