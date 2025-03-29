from typing import List, Dict, Optional
import torch
from transformers import AutoTokenizer
from pathlib import Path
import logging
import numpy as np
from dataclasses import dataclass

@dataclass
class CodeChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    embedding: Optional[np.ndarray] = None

class ContextManager:
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-1.3b-base"):
        self.logger = logging.getLogger(__name__)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.chunks: List[CodeChunk] = []
        
    def add_file(self, file_path: Path) -> None:
        """Parse and add a file to the context database."""
        try:
            content = file_path.read_text()
            chunks = self._split_into_chunks(content, str(file_path))
            self.chunks.extend(chunks)
            self.logger.info(f"Added {len(chunks)} chunks from {file_path}")
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")

    def get_relevant_context(self, query: str, max_chunks: int = 3) -> List[Dict[str, str]]:
        """Retrieve most relevant context chunks for a query."""
        if not self.chunks:
            return []
        
        # Simple relevance scoring based on token overlap
        scores = []
        query_tokens = set(self.tokenizer.tokenize(query))
        
        for chunk in self.chunks:
            chunk_tokens = set(self.tokenizer.tokenize(chunk.content))
            score = len(query_tokens.intersection(chunk_tokens))
            scores.append(score)
        
        # Get top chunks
        top_indices = np.argsort(scores)[-max_chunks:]
        return [
            {
                "content": self.chunks[i].content,
                "file": self.chunks[i].file_path,
                "lines": f"{self.chunks[i].start_line}-{self.chunks[i].end_line}"
            }
            for i in top_indices if scores[i] > 0
        ]

    def _split_into_chunks(self, content: str, file_path: str) -> List[CodeChunk]:
        """Split file content into semantic chunks."""
        lines = content.split("\n")
        chunks = []
        current_chunk = []
        current_start = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            
            # Simple heuristic: split on class/function definitions or after N lines
            if (line.strip().startswith(("class ", "def ")) and current_chunk) or \
               len(current_chunk) >= 50:
                chunks.append(CodeChunk(
                    content="\n".join(current_chunk),
                    file_path=file_path,
                    start_line=current_start,
                    end_line=i
                ))
                current_chunk = []
                current_start = i + 1
        
        # Add remaining lines
        if current_chunk:
            chunks.append(CodeChunk(
                content="\n".join(current_chunk),
                file_path=file_path,
                start_line=current_start,
                end_line=len(lines) - 1
            ))
        
        return chunks 