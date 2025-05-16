import os
import json

folder_path = "../../data/tasks"
old_model = "gpt-4o-mini"
new_model = "gpt-4.1-mini"

# Loop through all .jsonl files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".jsonl"):
        file_path = os.path.join(folder_path, filename)
        
        updated_lines = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                # Update the model field if it matches the old model name
                if data.get("body", {}).get("model") == old_model:
                    data["body"]["model"] = new_model
                updated_lines.append(json.dumps(data, ensure_ascii=False))

        # Overwrite the file with updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            for updated_line in updated_lines:
                f.write(updated_line + '\n')

print("Model name updated in all jsonl files.")
