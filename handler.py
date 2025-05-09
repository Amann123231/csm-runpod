import os
import sys
import base64
import io
import tempfile
import torch
import torchaudio
import runpod
from runpod.serverless.utils import download_files_from_urls

sys.path.append('/app/csm')

# Global variables to store the model
generator = None
initialized = False

def init():
    global generator, initialized
    
    if initialized:
        return
    
    # Check if HF_TOKEN is provided
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("ERROR: HF_TOKEN environment variable not set!")
        sys.exit(1)
    
    try:
        # Import the CSM generator
        from csm.generator import load_csm_1b
        
        # Initialize the model
        print("Loading CSM-1b model...")
        generator = load_csm_1b(device="cuda", hf_token=hf_token)
        print("CSM-1b model loaded successfully!")
        
        initialized = True
    except Exception as e:
        print(f"Error initializing model: {e}")
        sys.exit(1)

def handler(event):
    global generator
    
    # Initialize if not already done
    if not initialized:
        init()
    
    try:
        # Extract inputs
        inputs = event["input"]
        
        text = inputs.get("text", "")
        if not text:
            return {"error": "Text input is required"}
        
        speaker = inputs.get("speaker", 0)
        max_audio_length_ms = inputs.get("max_audio_length_ms", 10000)
        
        # Handle context if provided
        context = []
        if "context_audios" in inputs and isinstance(inputs["context_audios"], list):
            from csm.generator import Segment
            
            context_texts = inputs.get("context_texts", [])
            context_speakers = inputs.get("context_speakers", [])
            
            # Download context audio files
            audio_files = download_files_from_urls(inputs["context_audios"])
            
            # Create segments from context
            for i, audio_path in enumerate(audio_files):
                # Get corresponding text and speaker
                ctx_text = context_texts[i] if i < len(context_texts) else ""
                ctx_speaker = context_speakers[i] if i < len(context_speakers) else 0
                
                # Load audio
                audio_tensor, sample_rate = torchaudio.load(audio_path)
                audio_tensor = torchaudio.functional.resample(
                    audio_tensor.squeeze(0), 
                    orig_freq=sample_rate, 
                    new_freq=generator.sample_rate
                )
                
                # Create segment
                segment = Segment(
                    text=ctx_text,
                    speaker=ctx_speaker,
                    audio=audio_tensor
                )
                context.append(segment)
        
        # Generate audio
        print(f"Generating audio for text: {text}")
        audio = generator.generate(
            text=text,
            speaker=speaker,
            context=context,
            max_audio_length_ms=max_audio_length_ms
        )
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            torchaudio.save(
                temp_file.name, 
                audio.unsqueeze(0).cpu(), 
                generator.sample_rate
            )
            temp_file_path = temp_file.name
        
        # Read the file and encode as base64
        with open(temp_file_path, "rb") as audio_file:
            encoded_audio = base64.b64encode(audio_file.read()).decode("utf-8")
        
        # Clean up
        os.remove(temp_file_path)
        
        # Return the result
        return {
            "audio_base64": encoded_audio,
            "sample_rate": generator.sample_rate,
            "duration_seconds": audio.shape[0] / generator.sample_rate
        }
        
    except Exception as e:
        print(f"Error in handler: {e}")
        return {"error": str(e)}

# Start the RunPod serverless handler
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler}) 