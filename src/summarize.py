###############################################################################
##  `summarize.py`                                                           ##
##                                                                           ##
##  Purpose: Leverages BART Large CNN model to generate text summary         ##
###############################################################################


from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# Load model & tokenizer
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")


def summarize_text(text):
    # BART can handle ~1024 tokens, so chunk if needed
    max_chunk_length = 1024
    
    # Tokenize to check length
    tokens = tokenizer(text, return_tensors="pt", truncation=False)
    
    # If text fits in one chunk, summarize directly
    if tokens["input_ids"].shape[1] <= max_chunk_length:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_chunk_length)
        summary_ids = model.generate(inputs["input_ids"], max_length=150, min_length=40)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    
    # Otherwise, chunk the text by sentences to avoid losing content
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        test_chunk = current_chunk + sentence + ". "
        test_tokens = tokenizer(test_chunk, return_tensors="pt", truncation=False)
        
        if test_tokens["input_ids"].shape[1] <= max_chunk_length:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # Summarize each chunk
    summaries = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=max_chunk_length)
        summary_ids = model.generate(inputs["input_ids"], max_length=150, min_length=40)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summaries.append(summary)
    
    # Combine summaries (if short enough, return combined, otherwise summarize again)
    combined = " ".join(summaries)
    combined_tokens = tokenizer(combined, return_tensors="pt", truncation=False)
    
    if combined_tokens["input_ids"].shape[1] <= max_chunk_length:
        return combined
    else:
        # Recursively summarize combined summaries
        return summarize_text(combined)


def summarize_messages(messages_objs):
    # Combine message content with sender context
    combined_text = " ".join([
        f"{msg['sender_full_name']} said: {msg['content']}"
        for msg in messages_objs
    ])
    
    return summarize_text(combined_text)

