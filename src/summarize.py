###############################################################################
##  `summarize.py`                                                           ##
##                                                                           ##
##  Purpose: Leverages LLM to generate high-level conversation summaries     ##
###############################################################################


from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


# Load smaller instruction-tuned model for conversation summarization
model_name = "Qwen/Qwen2.5-3B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Set pad_token if not already set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)


def summarize_messages(messages_objs):    
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
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=8000)
    
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    # Generate summary
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
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


