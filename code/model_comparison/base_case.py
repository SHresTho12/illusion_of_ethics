import json
import os
from collections import defaultdict
from pathlib import Path

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

def process_base_case_category(category_name, file_mapping):
    """
    Process a specific category of base case files
    
    Args:
        category_name: Name of the category (e.g., 'immoral_action_moral_consequence', 'moral_action_immoral_consequence')
        file_mapping: Dictionary mapping model names to file paths
    """
    print(f"\n{'='*60}")
    print(f"PROCESSING: {category_name.upper().replace('_', ' ')}")
    print(f"{'='*60}")
    
    model_responses = {}
    
    for model_name, filepath in file_mapping.items():
        print(f"\nProcessing {model_name} file...")
        model_data = {}
        
        if filepath.exists():
            entries = read_jsonl_file(filepath)
            print(f"  Found {len(entries)} entries in {filepath.name}")
            
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
    output_file = output_dir / f'base_case_{category_name}_matching_ids.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save summary
    summary = {
        'category': category_name,
        'total_entries_per_model': {model: len(data) for model, data in model_responses.items()},
        'matching_counts': {pair: len(ids) for pair, ids in results.items()}
    }
    
    summary_file = output_dir / f'base_case_{category_name}_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*60)
    print("RESULTS SAVED")
    print("="*60)
    print(f"  - {output_file}")
    print(f"  - {summary_file}")
    
    return results, summary

def process_immoral_action_moral_consequence():
    """Process immoral action with moral consequence files"""
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    file_mapping = {
        'claude': results_dir / 'claude/Base Case/with_immoralAction_moralConsequence_base_claude.jsonl',
        'gemini': results_dir / 'gemini/Base Case/_result_with_immoralAction_moralConsequnece_base_prompts.jsonl',
        'gpt-4.1-mini': results_dir / 'GPT/gpt-4.1-mini/Base Case/with_immoralAction_moralConsequence_base_4.1_output.jsonl',
        'gpt-4-mini': results_dir / 'GPT/gpt-4-mini/Base Case/with_immoralAction_moralConsequence_base.jsonl'
    }
    
    model_responses = process_base_case_category('immoral_action_moral_consequence', file_mapping)
    return compare_models(model_responses, 'immoral_action_moral_consequence')

def process_moral_action_immoral_consequence():
    """Process moral action with immoral consequence files"""
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    file_mapping = {
        'claude': results_dir / 'claude/Base Case/with_moralAction_immoralConsequnece_base_claude.jsonl',
        'gemini': results_dir / 'gemini/Base Case/_result_with_moralAction_immoralConsequnece_base_prompts.jsonl',
        'gpt-4.1-mini': results_dir / 'GPT/gpt-4.1-mini/Base Case/with_moralAction_immoralConsequence_4.1_base_output.jsonl',
        'gpt-4-mini': results_dir / 'GPT/gpt-4-mini/Base Case/with_moralAction_immoralConsequence_base.jsonl'
    }
    
    model_responses = process_base_case_category('moral_action_immoral_consequence', file_mapping)
    return compare_models(model_responses, 'moral_action_immoral_consequence')

def main():
    print("="*60)
    print("BASE CASE ANALYSIS")
    print("="*60)
    
    # Process immoral action with moral consequence
    immoral_results, immoral_summary = process_immoral_action_moral_consequence()
    
    print("\n" + "="*60)
    print("IMMORAL ACTION - MORAL CONSEQUENCE SUMMARY")
    print("="*60)
    print(json.dumps(immoral_summary, indent=2))
    
    # Process moral action with immoral consequence
    moral_results, moral_summary = process_moral_action_immoral_consequence()
    
    print("\n" + "="*60)
    print("MORAL ACTION - IMMORAL CONSEQUENCE SUMMARY")
    print("="*60)
    print(json.dumps(moral_summary, indent=2))
    
    print("\n" + "="*60)
    print("ALL ANALYSES COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()