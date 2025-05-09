# CSM-1b on RunPod Serverless

This project sets up Sesame's CSM-1b speech generation model on RunPod's serverless infrastructure, allowing you to generate high-quality speech from text prompts through an API.

## Prerequisites

- A Hugging Face account with access to [sesame/csm-1b](https://huggingface.co/sesame/csm-1b)
- A RunPod account with API access
- Docker installed on your local machine

## Testing Your Hugging Face Token

Before building the Docker image, verify that your Hugging Face token has access to the CSM-1b model:

```bash
pip install huggingface_hub
python test_hf_token.py --token YOUR_HF_TOKEN
```

If successful, you'll see confirmation that your token can access the model.

## Building the Docker Image

1. Clone this repository:
```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

2. Build the Docker image:
```bash
docker build -t csm-1b-runpod .
```

## Pushing to Docker Hub

1. Tag your image:
```bash
docker tag csm-1b-runpod yourusername/csm-1b-runpod:latest
```

2. Push to Docker Hub:
```bash
docker login
docker push yourusername/csm-1b-runpod:latest
```

## Setting Up the RunPod Serverless Endpoint

1. Log in to your RunPod account
2. Go to Serverless > Endpoints
3. Click "New Endpoint"
4. Select "Docker Hub" and enter your image URL: `yourusername/csm-1b-runpod:latest`
5. Choose a GPU type (A10 or better recommended)
6. Set min/max workers based on your needs
7. Add the following environment variable:
   - Key: `HF_TOKEN`
   - Value: `YOUR_HUGGING_FACE_TOKEN`
8. Create the endpoint and wait for it to activate

## Using the Client

The included client script lets you interact with your serverless endpoint:

```bash
pip install requests pydub
python client.py --text "Hello from Sesame!" --endpoint YOUR_ENDPOINT_ID --api-key YOUR_RUNPOD_API_KEY
```

You can also set environment variables instead of passing arguments:

```bash
export RUNPOD_ENDPOINT_ID=YOUR_ENDPOINT_ID
export RUNPOD_API_KEY=YOUR_RUNPOD_API_KEY
python client.py --text "Hello from Sesame!"
```

## API Format

Your serverless endpoint accepts the following JSON input:

```json
{
  "input": {
    "text": "Hello, this is a test.",
    "speaker": 0,
    "max_audio_length_ms": 10000,
    "context_audios": ["https://example.com/audio1.wav"],
    "context_texts": ["Previous utterance"],
    "context_speakers": [1]
  }
}
```

The response will include:

```json
{
  "audio_base64": "base64-encoded WAV audio",
  "sample_rate": 24000,
  "duration_seconds": 1.5
}
```

## Troubleshooting

- **Model Loading Errors**: Ensure your Hugging Face token has accepted the model terms.
- **CUDA Out of Memory**: Try a larger GPU instance or reduce the max audio length.
- **Slow Generation**: The initial request will be slower as the model loads into memory.

## License

This project uses the Apache-2.0 license, in accordance with the CSM model license. 