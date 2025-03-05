# llm-streaming-guardrail

A microservices demo for streaming text generation with real‐time safety checks, following an Amazon Bedrock Guardrails pattern.

![guardrail](https://github.com/user-attachments/assets/93e2e0ee-5566-42e1-b0a2-37ab5c2b4fa9)

## Components

- **Gateway Service**  
  Receives OpenAI-compatible requests, streams responses from a vLLM server, buffers small text chunks (default 5 characters), and checks each chunk’s safety. Unsafe chunks are marked with “[UNSAFE]” in the SSE output.

- **Safety Service**  
  Uses a LLaMA Guard generative model to perform batch safety inference (default batch interval: 50ms) on incoming text chunks and returns a verdict ("safe" or "unsafe").

## Quick Start

### 1. Configure Environment Variables

#### vLLM Server Settings
- `VLLM_SERVER_URL`: URL of your vLLM server (e.g., `http://localhost:8001/v1/chat/completions`)
- `VLLM_MODEL`: Default model name (if not provided in the client request). Can be `None`.
- `VLLM_API_KEY`: API key for vLLM server authentication (optional)

#### Safety vLLM Server Settings
- `SAFETY_SERVICE_URL`: URL of the Safety Service (e.g., `http://localhost:8002/v1/chat/completions`)
- `SAFETY_MODEL`: Model used for safety evaluation (default: `llama-guard`)
- `SAFETY_API_KEY`: API key for Safety Service authentication (optional)
- `SAFETY_MODE`: Determines the safety check method. Options:
  - `"vllm"`: Uses a dedicated vLLM instance running LLaMA Guard for safety checks. (recommended)
  - `"separate"`: Uses an external Safety Service.

#### Streaming Settings
- `BUFFER_SIZE`: Number of characters to buffer before safety checking (default: `5`)
- `FLUSH_INTERVAL`: Time interval (in seconds) for flushing buffered text (default: `0.5`)

#### API Authentication
- `API_KEY`: Optional API key for request authentication (default: `mysecretapikey`)

### 2. Run the Services

Use Docker Compose:
```bash
docker-compose up --build
```

Or run each service separately:

- **Safety Service** on port **8002** (optional)
- **Gateway Service** on port **8000**
- Ensure your **vLLM server** is running on port **8001**

### 3. Test the API
Send a POST request to `http://localhost:8000/v1/chat/completions` with an OpenAI-compatible payload. The response will be streamed with real-time safety checks applied.

