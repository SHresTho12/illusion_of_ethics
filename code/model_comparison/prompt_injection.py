import json
import os
from pathlib import Path
from collections import defaultdict

def extract_custom_id_claude(entry):
    """Extract custom_id and response from Claude JSONL entry"""
    try:
        custom_id = entry.get('custom_id')
        response = entry['result']['message']['content'][0]['text']
        response_json = json.loads(response)
        return custom_id, response_json.get('response')
    except (KeyError, json.JSONDecodeError, IndexError):
        return None, None

def extract_custom_id_gemini(entry):
    """Extract custom_id and response from Gemini JSONL entry"""
    try:
        custom_id = entry.get('id')
        response = entry.get('result')
        return custom_id, response
    except KeyError:
        return None, None

def extract_custom_id_gpt(entry):
    """Extract custom_id and response from GPT JSONL entry"""
    try:
        custom_id = entry.get('custom_id')
        response = entry['response']['body']['choices'][0]['message']['content']
        response_json = json.loads(response)
        return custom_id, response_json.get('response')
    except (KeyError, json.JSONDecodeError, IndexError):
        return None, None

def read_jsonl_file(filepath):
    """Read JSONL file and return list of entries"""
    entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

def process_prompt_injection_category(category_name, file_mapping):
    """
    Process a specific category of prompt injection files
    
    Args:
        category_name: Name of the category (e.g., 'action_weighted', 'outcome_weighted')
        file_mapping: Dictionary mapping model names to file paths
    """
    print(f"\n{'='*60}")
    print(f"PROCESSING: {category_name.upper()}")
    print(f"{'='*60}")
    
    model_responses = {}
    
    for model_name, filepaths in file_mapping.items():
        print(f"\nProcessing {model_name} files...")
        model_data = {}
        
        for filepath in filepaths:
            if filepath.exists():
                entries = read_jsonl_file(filepath)
                for entry in entries:
                    if model_name == 'claude':
                        custom_id, response = extract_custom_id_claude(entry)
                    elif model_name == 'gemini':
                        custom_id, response = extract_custom_id_gemini(entry)
                    else:  # GPT models
                        custom_id, response = extract_custom_id_gpt(entry)
                    
                    if custom_id and response:
                        model_data[custom_id] = response
            else:
                print(f"  Warning: File not found - {filepath}")
        
        model_responses[model_name] = model_data
        print(f"{model_name}: {len(model_data)} entries")
    
    return model_responses

def compare_models(model_responses, category_name):
    """Compare models and save results"""
    
    # Get all custom_ids
    all_custom_ids = set()
    for model_data in model_responses.values():
        all_custom_ids.update(model_data.keys())
    
    # Compare pairs
    comparisons = [
        ('claude', 'gpt-4.1-mini'),
        ('claude', 'gpt-4-mini'),
        ('gpt-4.1-mini', 'gemini'),
        ('gpt-4-mini', 'gemini'),
        ('gemini', 'claude')
    ]
    
    results = {}
    
    print("\n" + "="*60)
    print("FINDING MATCHING RESPONSES")
    print("="*60)
    
    for model1, model2 in comparisons:
        matching_ids = []
        for custom_id in all_custom_ids:
            if custom_id in model_responses[model1] and custom_id in model_responses[model2]:
                if model_responses[model1][custom_id] == model_responses[model2][custom_id]:
                    matching_ids.append(custom_id)
        
        results[f"{model1}_vs_{model2}"] = matching_ids
        print(f"\n{model1} vs {model2}: {len(matching_ids)} matching responses")
        if len(matching_ids) <= 10:
            for cid in matching_ids:
                print(f"  - {cid}: {model_responses[model1][cid]}")
    
    # Save results
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    output_dir = results_dir / 'model_comparison'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    output_file = output_dir / f'prompt_injection_{category_name}_matching_ids.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save summary
    summary = {
        'category': category_name,
        'total_entries_per_model': {model: len(data) for model, data in model_responses.items()},
        'matching_counts': {pair: len(ids) for pair, ids in results.items()}
    }
    
    summary_file = output_dir / f'prompt_injection_{category_name}_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*60)
    print("RESULTS SAVED")
    print("="*60)
    print(f"  - {output_file}")
    print(f"  - {summary_file}")
    
    return results, summary

def process_action_weighted():
    """Process action-weighted prompt injection files"""
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    file_mapping = {
        'claude': [
            results_dir / 'claude/Prompt Injection/prompt_injection_immoral_act_action_weighted_claude_results.jsonl',
            results_dir / 'claude/Prompt Injection/prompt_injection_moral_action_action_weighted_claude.jsonl'
        ],
        'gemini': [
            results_dir / 'gemini/Prompt Injection/_result_prompt_injection_immoral_act_action_weighted.jsonl',
            results_dir / 'gemini/Prompt Injection/_result_prompt_injection_moral_action_action_weighted.jsonl'
        ],
        'gpt-4.1-mini': [
            results_dir / 'GPT/gpt-4.1-mini/Prompt Injection/prompt_injection_immoral_act_action_weighted_4.1.jsonl',
            results_dir / 'GPT/gpt-4.1-mini/Prompt Injection/prompt_injection_moralAction_immoralOutcome_prompts_tasks_4.1.jsonl'
        ],
        'gpt-4-mini': [
            results_dir / 'GPT/gpt-4-mini/Prompt Injection/prompt_injection_immoral_act_action_weighted.jsonl',
            results_dir / 'GPT/gpt-4-mini/Prompt Injection/prompt_injection_moral_action_action_weighted.jsonl'
        ]
    }
    
    model_responses = process_prompt_injection_category('action_weighted', file_mapping)
    return compare_models(model_responses, 'action_weighted')

def process_outcome_weighted():
    """Process outcome-weighted prompt injection files"""
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    file_mapping = {
        'claude': [
            results_dir / 'claude/Prompt Injection/prompt_injection_immoral_action_outcome_weighted_claude.jsonl',
            results_dir / 'claude/Prompt Injection/Prompt_injection_moral_action_outcome_weighted_claude.jsonl'
        ],
        'gemini': [
            results_dir / 'gemini/Prompt Injection/_result_prompt_injection_immoral_action_outcome_weighted.jsonl',
            results_dir / 'gemini/Prompt Injection/_result_Prompt_injection_moral_action_outcome_weighted.jsonl'
        ],
        'gpt-4.1-mini': [
            results_dir / 'GPT/gpt-4.1-mini/Prompt Injection/prompt_injection_immoral_action_outcome_weighted_4.1.jsonl',
            results_dir / 'GPT/gpt-4.1-mini/Prompt Injection/Prompt_injection_moral_action_outcome_weighted_4.1.jsonl'
        ],
        'gpt-4-mini': [
            results_dir / 'GPT/gpt-4-mini/Prompt Injection/prompt_injection_immoral_action_outcome_weighted.jsonl',
            results_dir / 'GPT/gpt-4-mini/Prompt Injection/Prompt_injection_moral_action_outcome_weighted.jsonl'
        ]
    }
    
    model_responses = process_prompt_injection_category('outcome_weighted', file_mapping)
    return compare_models(model_responses, 'outcome_weighted')

def main():
    print("="*60)
    print("PROMPT INJECTION ANALYSIS")
    print("="*60)
    
    # Process action-weighted
    action_results, action_summary = process_action_weighted()
    
    print("\n" + "="*60)
    print("ACTION-WEIGHTED SUMMARY")
    print("="*60)
    print(json.dumps(action_summary, indent=2))
    
    # Process outcome-weighted
    outcome_results, outcome_summary = process_outcome_weighted()
    
    print("\n" + "="*60)
    print("OUTCOME-WEIGHTED SUMMARY")
    print("="*60)
    print(json.dumps(outcome_summary, indent=2))
    
    print("\n" + "="*60)
    print("ALL ANALYSES COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()