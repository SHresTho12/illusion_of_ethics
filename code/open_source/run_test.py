import argparse
import os
import logging
import json
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm
import re

# Configuration
DATASETS_DIR = Path("../../data/prompts")
RESULTS_BASE_DIR = Path("../../results/open_source")
MODELS_DIR = Path("Models")

# Prompt type to file mapping
PROMPT_FILES = {
    "choice_with_norm": "choice_prompts_with_norm.jsonl",
    "choice_without_norm": "choice_prompts_without_norm.jsonl",
    "immoral_with_norm": "immoral_act_with_norm_prompts.jsonl",
    "immoral_without_norm": "immoral_act_without_norm_prompts.jsonl",
    "moral_action_immoral_outcome": "with_moralAction_immoralConsequnece_base_prompts.jsonl",
    "immoral_action_moral_outcome": "with_immoralAction_moralConsequnece_base_prompts.jsonl",
    "injection_moral_action_immoral_outcome": "injection_moralAction_immoralOutcome_prompts.jsonl",
    "pro_action_immoral": "anti_action_immoralAction_prompts.jsonl",
    "pro_outcome_immoral": "pro_outcome_immoralAction_prompts.jsonl",
    "outcome_weighted_moral": "outcome_weighted_moralAction_prompts.jsonl"
}


class ModelRunner:
    def __init__(self, model_name, device="auto", max_new_tokens=50):
        self.original_model_name = model_name
        self.max_new_tokens = max_new_tokens

        # Resolve local path
        self.model_path = MODELS_DIR / model_name.replace("/", "_")

        if self.model_path.exists():
            logging.info(f"Loading model from local path: {self.model_path}")
            load_path = str(self.model_path)
        else:
            logging.info(f"Model not found locally. Downloading: {model_name}")
            load_path = model_name  # download from HF

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            load_path,
            trust_remote_code=True,
            padding_side='left'
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            load_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=device,
            trust_remote_code=True
        )

        # If downloaded, save locally
        if not self.model_path.exists():
            logging.info(f"Saving model locally to {self.model_path}")
            self.model.save_pretrained(self.model_path)
            self.tokenizer.save_pretrained(self.model_path)

        self.model.eval()
        logging.info(f"Model ready on {self.model.device}")
    
    def generate_response(self, prompt):
        """
        Generate response from the model
        
        Args:
            prompt: Input prompt string
            
        Returns:
            Generated text response
        """
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode only the generated part (excluding input prompt)
        generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return response.strip()
    
    def extract_json_response(self, text):
        """
        Extract JSON response from model output
        
        Args:
            text: Model output text
            
        Returns:
            Extracted response value or None
        """
        # Try to find JSON-like structure
        json_patterns = [
            r'\{[^}]*"response"[^}]*:\s*"?([0-2])"?[^}]*\}',
            r'"response"[^}]*:\s*"?([0-2])"?',
            r'\{[^}]*:\s*"?([0-2])"?[^}]*\}',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try to find standalone digit
        digit_match = re.search(r'\b([0-2])\b', text)
        if digit_match:
            return digit_match.group(1)
        
        return None


def load_existing_results(output_file):
    """
    Load existing results from output file
    
    Args:
        output_file: Path to output file
        
    Returns:
        Set of processed IDs
    """
    processed_ids = set()
    
    if output_file.exists():
        with open(output_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        processed_ids.add(entry.get('id') or entry.get('custom_id'))
                    except json.JSONDecodeError:
                        continue
    
    return processed_ids


def read_prompts(prompt_file):
    """
    Read prompts from JSONL file
    
    Args:
        prompt_file: Path to prompt file
        
    Returns:
        List of prompt dictionaries
    """
    prompts = []
    with open(prompt_file, 'r') as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))
    return prompts

def save_result(output_file, custom_id, prompt_text, response_value, raw_response=None):
    result = {
        "id": custom_id,
        "prompt": prompt_text,
        "result": response_value
    }

    # Optional but VERY useful for debugging
    if raw_response is not None:
        result["raw_response"] = raw_response

    with open(output_file, 'a') as f:
        f.write(json.dumps(result) + '\n')


def process_dataset(model_runner, prompt_type, output_dir, resume=True):
    """
    Process a dataset with the model
    
    Args:
        model_runner: ModelRunner instance
        prompt_type: Type of prompt to process
        output_dir: Output directory for results
        resume: Whether to resume from existing results
    """
    # Get prompt file
    prompt_file = DATASETS_DIR / PROMPT_FILES[prompt_type]
    
    if not prompt_file.exists():
        logging.warning(f"Prompt file not found: {prompt_file}")
        return
    
    # Set up output file
    output_file = output_dir / f"_result_{PROMPT_FILES[prompt_type]}"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing results if resuming
    processed_ids = load_existing_results(output_file) if resume else set()
    
    # Read prompts
    prompts = read_prompts(prompt_file)
    
    logging.info(f"Processing {prompt_type}: {len(prompts)} total prompts")
    if processed_ids:
        logging.info(f"Resuming: {len(processed_ids)} already processed")
    
    # Process prompts
    failed_prompts = []
    
    for prompt_data in tqdm(prompts, desc=f"Processing {prompt_type}"):
        custom_id = prompt_data.get('ID')
        
        # Skip if already processed
        if custom_id in processed_ids:
            continue
        
        try:
            # Get prompt text
            prompt_text = prompt_data.get('prompt')
            
            if not prompt_text:
                logging.warning(f"No prompt found for ID: {custom_id}")
                continue
            
            # Generate response
            raw_response = model_runner.generate_response(prompt_text)
            
            # Extract structured response
            response_value = model_runner.extract_json_response(raw_response)
            
            if response_value is None:
                logging.warning(f"Could not extract response for ID: {custom_id}, raw: {raw_response[:100]}")
                failed_prompts.append({
                    'id': custom_id,
                    'raw_response': raw_response
                })
                # Save with None to mark as attempted
                response_value = "None"
            
            # Save result immediately
            save_result(
                output_file,
                custom_id,
                prompt_text,
                response_value,
                raw_response)
            processed_ids.add(custom_id)
            
        except Exception as e:
            logging.error(f"Error processing ID {custom_id}: {str(e)}")
            failed_prompts.append({
                'id': custom_id,
                'error': str(e)
            })
    
    # Save failed prompts log
    if failed_prompts:
        failed_file = output_dir / f"_failed_{PROMPT_FILES[prompt_type]}"
        with open(failed_file, 'w') as f:
            for failed in failed_prompts:
                f.write(json.dumps(failed) + '\n')
        logging.warning(f"Failed prompts saved to: {failed_file}")
    
    logging.info(f"Completed {prompt_type}: {len(processed_ids)} total processed")


def main():
    parser = argparse.ArgumentParser(description='Run open-source models on moral reasoning tasks')
    parser.add_argument("model_name", type=str, help="HuggingFace model name (e.g., 'meta-llama/Llama-2-7b-chat-hf')")
    parser.add_argument("--prompt_types", type=str, nargs='+', 
                       help="Specific prompt types to process (default: all)",
                       choices=list(PROMPT_FILES.keys()))
    parser.add_argument("--device", type=str, default="auto", 
                       help="Device to run on (auto, cuda, cpu)")
    parser.add_argument("--max_new_tokens", type=int, default=50,
                       help="Maximum tokens to generate")
    parser.add_argument("--no_resume", action="store_true",
                       help="Don't resume from existing results (start fresh)")
    parser.add_argument("--logging", type=str, default="info",
                       choices=["debug", "info", "warning", "error", "off"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.logging != "off":
        log_level = getattr(logging, args.logging.upper())
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
    
    # Create model-specific output directory
    model_safe_name = args.model_name.replace('/', '_')
    output_dir = RESULTS_BASE_DIR / model_safe_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Results will be saved to: {output_dir}")
    
    # Initialize model
    model_runner = ModelRunner(
        args.model_name,
        device=args.device,
        max_new_tokens=args.max_new_tokens
    )
    
    # Determine which prompt types to process
    prompt_types = args.prompt_types if args.prompt_types else list(PROMPT_FILES.keys())
    
    # Process each prompt type
    for prompt_type in prompt_types:
        try:
            process_dataset(
                model_runner,
                prompt_type,
                output_dir,
                resume=not args.no_resume
            )
        except Exception as e:
            logging.error(f"Error processing {prompt_type}: {str(e)}")
            continue
    
    logging.info("All processing complete!")


if __name__ == "__main__":
    main()