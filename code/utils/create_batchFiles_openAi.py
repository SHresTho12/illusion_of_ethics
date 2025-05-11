import json
import os
from config import PROMPT_FILES, BATCH_DIR

def create_batch_jsonl(original_file):
    filename = os.path.basename(original_file)  
    base, ext = os.path.splitext(filename)
    if ext != '.jsonl':
        raise ValueError(f"File {filename} is not a .jsonl file")
    if not os.path.exists(BATCH_DIR):
        os.makedirs(BATCH_DIR)
    new_file = os.path.join(BATCH_DIR, f"{base}_batch{ext}")  # Save in batch dir

    question_text = None

    with open(original_file, 'r', encoding='utf-8') as infile, \
         open(new_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            if not line.strip():
                continue  # Skip empty lines
            data = json.loads(line)

            full_prompt = data.get("prompt", "")
            parts = full_prompt.split("Question:")
            main_prompt = parts[0].strip()

            if question_text is None and len(parts) > 1:
                question_text = parts[1].strip()

            id_ = data.get("ID") or data.get("id")
            new_obj = {
                "id": id_,
                "prompt": main_prompt
            }

            outfile.write(json.dumps(new_obj) + '\n')

    print(f"Batch file created: {new_file}")
    return new_file, {"question": question_text, "file": filename}



def generate_all_batches():
    all_questions = {}

    for key, file_path in PROMPT_FILES.items():
        print(f"Processing: {key}")
        batch_file, question_text = create_batch_jsonl(file_path)
        all_questions[key] = question_text

    return all_questions  
