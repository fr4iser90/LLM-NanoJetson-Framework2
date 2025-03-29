from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
    context_chunks: Optional[List[Dict[str, str]]] = None

class GenerationResponse(BaseModel):
    request_id: str
    status: str
    generated_code: str
    metadata: Dict

app = FastAPI(title="AutoCoder LLM Server")
logger = logging.getLogger(__name__)

class LLMServer:
    def __init__(self, model_path: str, device: str = "cuda"):
        self.device = "cuda" if torch.cuda.is_available() and device == "cuda" else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        logger.info("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            device_map="auto"
        )
        logger.info("Model loaded successfully")

    async def generate(self, request: GenerationRequest) -> str:
        try:
            # Prepare prompt with context
            full_prompt = self._prepare_prompt(request)
            
            # Tokenize
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=request.max_tokens,
                    temperature=request.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode and return
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text[len(full_prompt):]  # Remove the prompt from response
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _prepare_prompt(self, request: GenerationRequest) -> str:
        prompt = request.prompt
        if request.context_chunks:
            context = "\n".join(chunk["content"] for chunk in request.context_chunks)
            prompt = f"{context}\n\n{prompt}"
        return prompt

# Global LLM server instance
llm_server = None

@app.on_event("startup")
async def startup_event():
    global llm_server
    model_path = "deepseek-ai/deepseek-coder-1.3b-base"  # Can be configured via env
    llm_server = LLMServer(model_path)

@app.post("/generate", response_model=GenerationResponse)
async def generate_code(request: GenerationRequest):
    if not llm_server:
        raise HTTPException(status_code=500, detail="LLM server not initialized")
    
    generated_code = await llm_server.generate(request)
    
    return GenerationResponse(
        request_id=str(uuid.uuid4()),
        status="success",
        generated_code=generated_code,
        metadata={
            "model": "deepseek-coder-1.3b",
            "token_count": len(request.prompt.split()),
            "temperature": request.temperature
        }
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "gpu_available": torch.cuda.is_available()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 