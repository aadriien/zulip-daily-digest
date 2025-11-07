###############################################################################
##  `summarize.py`                                                           ##
##                                                                           ##
##  Purpose: Leverages LLM to generate high-level conversation summaries     ##
###############################################################################


import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


# Lazy load model only when needed
_model = None
_tokenizer = None

def _get_model_and_tokenizer():
    global _model, _tokenizer
    
    if _model is None or _tokenizer is None:
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "Qwen2.5-1.5B-Instruct")
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Set pad_token if not already set
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float32, # Use float32 for CPU to avoid issues
            device_map="cpu",
            low_cpu_mem_usage=True
        )
    
    return _model, _tokenizer


def summarize_messages(messages_objs):    
    # Lazy-load to avoid memory spike at import
    model, tokenizer = _get_model_and_tokenizer()

    # Format messages as natural conversation
    formatted_messages = []
    for msg in messages_objs:
        formatted_messages.append(f"{msg['sender_full_name']}: {msg['content']}")
    
    conversation = "\n".join(formatted_messages)
    
    system_prompt = """You are a helpful assistant that summarizes Zulip channel conversations. 
Provide a concise high-level overview of what was discussed. Focus on:
- Main topics and themes
- Key decisions or outcomes
- Important questions raised

Do NOT quote individuals directly or use "X said Y" format. Write in narrative form."""
    
    user_prompt = f"""Summarize this channel conversation:

{conversation}

Provide a brief high-level summary (1-2 sentences) of what took place.
Be as concise as possible. The shorter the better. Do NOT write more than 1 sentence."""
    
    # Format as instruction chat
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Apply chat template & tokenize with truncation (Qwen2.5 has 32k context)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4000)

    # Force CPU tensors to avoid accidental GPU OOM / CUDA init
    inputs = {k: v.to("cpu") for k, v in inputs.items()}
    
    # Generate summary
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=120,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode only newly generated tokens (skip input prompt)
    input_length = inputs['input_ids'].shape[1]
    generated_tokens = outputs[0][input_length:]
    
    summary = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    
    return summary


