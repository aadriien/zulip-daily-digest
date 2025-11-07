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


def _summarize_chunk(model, tokenizer, conversation_text, is_final_summary=False, is_long_conversation=False):
    system_prompt = """You are a helpful assistant that summarizes Zulip channel conversations. 
Provide a concise overview of what was discussed. Focus on:
- Main topics and themes
- Key decisions or outcomes
- Important questions raised

Write in narrative form."""
    
    if is_final_summary:
        if is_long_conversation:
            user_prompt = f"""Summarize these conversation summaries:

{conversation_text}

Provide a summary in 2 sentences maximum. Separate sentences with newlines if using multiple sentences."""
        else:
            user_prompt = f"""Summarize these conversation summaries:

{conversation_text}

Provide a brief summary in 1 sentence."""
    else:
        if is_long_conversation:
            user_prompt = f"""Summarize this channel conversation:

{conversation_text}

Provide a summary in 2 sentences maximum. Separate sentences with newlines if using multiple sentences."""
        else:
            user_prompt = f"""Summarize this channel conversation:

{conversation_text}

Provide a brief summary in 1 sentence."""
    
    # Format as instruction chat
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Apply chat template & tokenize WITHOUT truncation
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=False)

    # Force CPU tensors to avoid accidental GPU OOM / CUDA init
    inputs = {k: v.to("cpu") for k, v in inputs.items()}
    
    # Generate summary
    max_tokens = 200 if is_long_conversation else 120
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
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


def summarize_messages(messages_objs):    
    # Lazy-load to avoid memory spike at import
    model, tokenizer = _get_model_and_tokenizer()

    # Format messages as natural conversation
    formatted_messages = []
    for msg in messages_objs:
        formatted_messages.append(f"{msg['sender_full_name']}: {msg['content']}")
    
    conversation = "\n".join(formatted_messages)
    
    # Conservative limit: leave room for prompts & generation
    # Model supports 32k, so use 14k for conversation to be safe
    MAX_CONVERSATION_TOKENS = 14000
    
    # Check if conversation fits within token limit
    test_prompt_tokens = tokenizer(conversation, return_tensors="pt", truncation=False)
    conversation_token_count = test_prompt_tokens['input_ids'].shape[1]
    
    # Determine if long conversation (>7k tokens = roughly 50-60 messages)
    is_long_conversation = conversation_token_count > 7000
    
    # If conversation fits, summarize directly
    if conversation_token_count <= MAX_CONVERSATION_TOKENS:
        return _summarize_chunk(model, tokenizer, conversation, is_long_conversation=is_long_conversation)
    
    # Otherwise, chunk conversation & summarize in parts
    print(f"  → Conversation too long ({conversation_token_count} tokens), processing in chunks...")
    
    # Split messages into chunks that fit within token limit
    chunk_summaries = []
    current_chunk = []
    current_chunk_text = ""
    
    for formatted_msg in formatted_messages:
        test_chunk = "\n".join(current_chunk + [formatted_msg])
        test_tokens = tokenizer(test_chunk, return_tensors="pt", truncation=False)
        
        if test_tokens['input_ids'].shape[1] > MAX_CONVERSATION_TOKENS:
            # Current chunk full, so summarize it
            if current_chunk:
                chunk_text = "\n".join(current_chunk)
                chunk_summary = _summarize_chunk(model, tokenizer, chunk_text, is_long_conversation=is_long_conversation)
                chunk_summaries.append(chunk_summary)

                print(f"  → Summarized chunk of {len(current_chunk)} messages")
            
            # Start new chunk with current message
            current_chunk = [formatted_msg]
        else:
            current_chunk.append(formatted_msg)
    
    # Summarize any remaining messages
    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        chunk_summary = _summarize_chunk(model, tokenizer, chunk_text, is_long_conversation=is_long_conversation)
        chunk_summaries.append(chunk_summary)

        print(f"  → Summarized final chunk of {len(current_chunk)} messages")
    
    # If only ended up with single chunk, return it directly
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]
    
    # Otherwise create summary of summaries
    print(f"  → Creating final summary from {len(chunk_summaries)} chunk summaries")

    combined_summaries = "\n\n".join([f"Part {i+1}: {s}" for i, s in enumerate(chunk_summaries)])
    final_summary = _summarize_chunk(model, tokenizer, combined_summaries, is_final_summary=True, is_long_conversation=is_long_conversation)
    
    return final_summary


