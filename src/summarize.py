###############################################################################
##  `summarize.py`                                                           ##
##                                                                           ##
##  Purpose: Leverages LLM to generate high-level conversation summaries     ##
###############################################################################


from src.model import get_model_tokenizer, generate_text


# Summarization constants
MAX_CONVERSATION_TOKENS = 14000
LONG_CONVERSATION_THRESHOLD = 7000


def _dedent(s):
    # Strip leading / trailing whitespace & remove indentation
    lines = s.strip().split("\n")
    if not lines:
        return ""
    
    indent = len(lines[0]) - len(lines[0].lstrip())

    return "\n".join(
        line[indent:] 
        if line.startswith(" " * indent) 
        else line 
        for line in lines
    )


def _build_summary_prompt(conversation_text, is_final_summary, is_long_conversation):
    system_prompt = _dedent("""
        You are a helpful assistant that summarizes Zulip channel conversations. 
        Provide a concise overview of what was discussed. Focus on:
        - Main topics and themes
        - Key decisions or outcomes
        - Important questions raised
        
        Write in narrative form.
    """)
    
    # Choose prompt based on summary type & conversation length
    if is_final_summary:
        if is_long_conversation:
            user_prompt = _dedent(f"""
                Summarize these conversation summaries:
                
                {conversation_text}
                
                Provide a summary in 2 sentences maximum. 
                Separate sentences with newlines if using multiple sentences.
            """)
        else:
            user_prompt = _dedent(f"""
                Summarize these conversation summaries:
                
                {conversation_text}
                
                Provide a brief summary in 1 sentence.
            """)
    else:
        if is_long_conversation:
            user_prompt = _dedent(f"""
                Summarize this channel conversation:
                
                {conversation_text}
                
                Provide a summary in 2 sentences maximum. 
                Separate sentences with newlines if using multiple sentences.
            """)
        else:
            user_prompt = _dedent(f"""
                Summarize this channel conversation:
                
                {conversation_text}
                
                Provide a brief summary in 1 sentence.
            """)
    
    return system_prompt, user_prompt


def _summarize_chunk(model, tokenizer, conversation_text, is_final_summary=False, is_long_conversation=False):
    system_prompt, user_prompt = _build_summary_prompt(
        conversation_text, 
        is_final_summary, 
        is_long_conversation
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    max_tokens = 200 if is_long_conversation else 120
    summary = generate_text(tokenizer, model, messages, max_new_tokens=max_tokens)
    
    return summary


def _format_messages_as_conversation(messages_objs):
    formatted_messages = []

    for msg in messages_objs:
        formatted_messages.append(f"{msg['sender_full_name']}: {msg['content']}")

    return formatted_messages


def _chunk_and_summarize(model, tokenizer, formatted_messages, is_long_conversation):
    chunk_summaries = []
    current_chunk = []
    
    for formatted_msg in formatted_messages:
        test_chunk = "\n".join(current_chunk + [formatted_msg])
        test_tokens = tokenizer(test_chunk, return_tensors="pt", truncation=False)
        
        if test_tokens['input_ids'].shape[1] > MAX_CONVERSATION_TOKENS:
            # Current chunk full, so summarize it
            if current_chunk:
                chunk_text = "\n".join(current_chunk)

                chunk_summary = _summarize_chunk(
                    model, tokenizer, 
                    chunk_text, 
                    is_long_conversation=is_long_conversation
                )
                chunk_summaries.append(chunk_summary)

                print(f"  → Summarized chunk of {len(current_chunk)} messages")
            
            # Start new chunk with current message
            current_chunk = [formatted_msg]
        else:
            current_chunk.append(formatted_msg)
    
    # Summarize any remaining messages
    if current_chunk:
        chunk_text = "\n".join(current_chunk)

        chunk_summary = _summarize_chunk(
            model, tokenizer, 
            chunk_text, 
            is_long_conversation=is_long_conversation
        )
        chunk_summaries.append(chunk_summary)

        print(f"  → Summarized final chunk of {len(current_chunk)} messages")

    return chunk_summaries


def summarize_messages(messages_objs):
    model, tokenizer = get_model_tokenizer()
    
    # Format messages as natural conversation
    formatted_messages = _format_messages_as_conversation(messages_objs)
    conversation = "\n".join(formatted_messages)
    
    # Check if conversation fits within token limit
    test_tokens = tokenizer(conversation, return_tensors="pt", truncation=False)
    conversation_token_count = test_tokens['input_ids'].shape[1]
    is_long_conversation = conversation_token_count > LONG_CONVERSATION_THRESHOLD
    
    # If conversation fits, summarize directly
    if conversation_token_count <= MAX_CONVERSATION_TOKENS:
        return _summarize_chunk(
            model, tokenizer, 
            conversation, 
            is_long_conversation=is_long_conversation
        )
    
    # Otherwise chunk & summarize in parts
    print(f"  → Conversation too long ({conversation_token_count} tokens), processing in chunks...")
    chunk_summaries = _chunk_and_summarize(
        model, tokenizer, 
        formatted_messages, 
        is_long_conversation
    )
    
    # If only one chunk, return it directly
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]
    
    # Create summary of summaries
    print(f"  → Creating final summary from {len(chunk_summaries)} chunk summaries")
    
    combined_summaries = "\n\n".join([
        f"Part {i+1}: {s}" 
        for i, s in enumerate(chunk_summaries)
    ])
    final_summary = _summarize_chunk(
        model, tokenizer, 
        combined_summaries, 
        is_final_summary=True, 
        is_long_conversation=is_long_conversation
    )
    
    return final_summary


