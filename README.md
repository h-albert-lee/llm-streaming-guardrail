# llm-streaming-guardrail
LLM Streaming Guardrail with Amazon Bedrock Guardrails Pattern

This project demonstrates a microservices architecture for streaming text generation with real-time safety checks. It consists of two main services:

## Gateway Service:
Receives OpenAI-compatible requests, streams text from a vLLM server, buffers small text chunks (default 5 characters), and sends each chunk to the Safety Service for safety checking. It then returns an SSE stream to the client.

## Safety Service:
Uses a LLaMA Guard generative model to perform batch inference on incoming text chunks, and returns a safety verdict ("safe" or "unsafe").