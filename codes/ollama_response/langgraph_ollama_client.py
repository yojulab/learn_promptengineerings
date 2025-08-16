#!/usr/bin/env python3
"""
LangGraph-based Ollama client implementation
Handles model request and response with structured key-based output
"""

import asyncio
from typing import Dict, Any, TypedDict
from dataclasses import dataclass
import httpx
from langgraph.graph import StateGraph, END


class OllamaState(TypedDict):
    """State for LangGraph workflow"""
    model: str
    prompt: str
    stream: bool
    response_data: Dict[str, Any]
    error: str
    status: str


@dataclass
class OllamaRequest:
    """Ollama API request configuration"""
    model: str = "gemma3:1b"
    prompt: str = ""
    stream: bool = False
    url: str = "http://localhost:11434/api/generate"


class OllamaClient:
    """LangGraph-based Ollama client"""
    
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(OllamaState)
        
        # Add nodes
        workflow.add_node("prepare_request", self._prepare_request)
        workflow.add_node("make_request", self._make_request)
        workflow.add_node("process_response", self._process_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Define edges
        workflow.set_entry_point("prepare_request")
        workflow.add_edge("prepare_request", "make_request")
        workflow.add_conditional_edges(
            "make_request",
            self._check_request_status,
            {
                "success": "process_response",
                "error": "handle_error"
            }
        )
        workflow.add_edge("process_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    async def _prepare_request(self, state: OllamaState) -> OllamaState:
        """Prepare the request"""
        print("🔧 [PREPARE] Setting up request parameters")
        state["status"] = "preparing"
        return state
    
    async def _make_request(self, state: OllamaState) -> OllamaState:
        """Make HTTP request to Ollama API"""
        print("📡 [REQUEST] Sending to Ollama API")
        
        request_data = {
            "model": state["model"],
            "prompt": state["prompt"],
            "stream": state["stream"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json=request_data
                )
                response.raise_for_status()
                state["response_data"] = response.json()
                state["status"] = "success"
                
        except httpx.RequestError as e:
            state["error"] = f"Request error: {str(e)}"
            state["status"] = "error"
        except httpx.HTTPStatusError as e:
            state["error"] = f"HTTP error: {e.response.status_code}"
            state["status"] = "error"
        except Exception as e:
            state["error"] = f"Unexpected error: {str(e)}"
            state["status"] = "error"
            
        return state
    
    async def _process_response(self, state: OllamaState) -> OllamaState:
        """Process successful response"""
        print("✅ [PROCESS] Processing response data")
        
        response_data = state["response_data"]
        
        # Print response keys separately
        print("\n📊 [RESPONSE_KEYS] Response structure:")
        for key, value in response_data.items():
            if key == "context":
                print(f"  {key}: [array with {len(value)} elements]")
            elif key == "response":
                print(f"  {key}: {value}")
            elif key in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
                # Convert nanoseconds to milliseconds for readability
                ms_value = value / 1_000_000
                print(f"  {key}: {ms_value:.2f}ms")
            else:
                print(f"  {key}: {value}")
        
        state["status"] = "completed"
        return state
    
    async def _handle_error(self, state: OllamaState) -> OllamaState:
        """Handle errors"""
        print(f"❌ [ERROR] {state['error']}")
        return state
    
    def _check_request_status(self, state: OllamaState) -> str:
        """Check if request was successful"""
        return state["status"]
    
    async def generate(self, model: str = "gemma3:1b", prompt: str = "", stream: bool = False) -> Dict[str, Any]:
        """Generate response using Ollama API"""
        initial_state = OllamaState(
            model=model,
            prompt=prompt,
            stream=stream,
            response_data={},
            error="",
            status="pending"
        )
        
        print(f"🚀 [START] Generating response with model: {model}")
        print(f"📝 [PROMPT] {prompt}")
        
        result = await self.workflow.ainvoke(initial_state)
        return result


async def main():
    """Main function to demonstrate usage"""
    client = OllamaClient()
    
    # Example request with system and user prompts separated
    system_prompt = "당신은 간결하고 정확한 답변을 제공하는 AI 어시스턴트입니다."
    user_prompt = "Hello, what is FastAPI? 3단어로 작성"
    
    combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
    
    result = await client.generate(
        model="gemma3:1b",
        prompt=combined_prompt,
        stream=False
    )
    
    print(f"\n🏁 [FINAL_STATUS] {result['status']}")
    
    if result["status"] == "completed":
        print("\n🎯 [SUCCESS] Request completed successfully")
        response_text = result["response_data"].get("response", "")
        print(f"💬 [AI_RESPONSE] {response_text}")
    else:
        print(f"\n💥 [FAILED] {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())