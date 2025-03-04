# llm-streaming-guardrail

A microservices demo for streaming text generation with real‐time safety checks, following an Amazon Bedrock Guardrails pattern.

## Components

- **Gateway Service**  
  Receives OpenAI-compatible requests, streams responses from a vLLM server, buffers small text chunks (default 5 characters), and checks each chunk’s safety. Unsafe chunks are marked with “[UNSAFE]” in the SSE output.

- **Safety Service**  
  Uses a LLaMA Guard generative model to perform batch safety inference (default batch interval: 50ms) on incoming text chunks and returns a verdict ("safe" or "unsafe").

## Quick Start

1. **Configure Environment Variables:**  
   - `VLLM_SERVER_URL`: URL of your vLLM server (e.g., `http://localhost:8001/v1/chat/completions`)
   - `SAFETY_SERVICE_URL`: URL of your Safety Service (e.g., `http://localhost:8002/v1/chat/completions`)
   - `SAFETY_MODE`: Either `"separate"` (use separate Safety Service) or `"vllm"` (use vLLM instance running Llama Guard)
   - `BUFFER_SIZE`: Default is 5 characters
   - `FLUSH_INTERVAL`: Default is 0.5 seconds
   - `API_KEY`: Your API key for authentication

2. **Run the Services:**  
   Use Docker Compose:
   ```bash
   docker-compose up --build
   ```

   Or run each service separately:

- **Safety Service** on port **8002**
- **Gateway Service** on port **8000**
- Ensure your **vLLM server** is running on port **8001**

Test the API:
POST an OpenAI-compatible request to `http://localhost:8000/v1/chat/completions` and receive an SSE stream with safety-checked text.

