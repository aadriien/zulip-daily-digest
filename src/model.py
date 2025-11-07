###############################################################################
##  `model.py`                                                               ##
##                                                                           ##
##  Purpose: Handles LLM loading & text generation                           ##
###############################################################################


import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# Lazy load model only when needed
_model = None
_tokenizer = None


def get_model_tokenizer():
    global _model, _tokenizer
    
    if _model is None or _tokenizer is None:
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "models", "Qwen2.5-1.5B-Instruct"
        )
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Set pad_token if not already set
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
    
    return _model, _tokenizer


def generate_text(tokenizer, model, messages, max_new_tokens=120):
    # Apply chat template & tokenize without truncation
    prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt", truncation=False)
    inputs = {k: v.to("cpu") for k, v in inputs.items()}
    
    # Generate text
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode only the generated tokens
    input_length = inputs['input_ids'].shape[1]
    generated_tokens = outputs[0][input_length:]

    text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    return text


