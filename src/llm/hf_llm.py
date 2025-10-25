"""Hugging Face Transformers LLM interface (Qwen, etc.)"""

from __future__ import annotations

from typing import Any, Dict, List
import json
import re

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


def init_llm_hf(model_name: str) -> tuple[Any, Any]:
    """Initialize Transformers model and tokenizer on CPU."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def generate_response_hf(
    model: Any, tokenizer: Any, prompt: str, max_tokens: int = 512
) -> str:
    """Generate response using the model."""
    try:
        inputs = tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        )

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=False,
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        return response.strip()
    except Exception as e:
        print(f"Generation failed: {e}")
        return ""


def format_qwen_prompt(system_prompt: str, user_prompt: str) -> str:
    """Format prompt in Qwen chat template."""
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
