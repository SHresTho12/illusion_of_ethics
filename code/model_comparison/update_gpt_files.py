import json
import os
from pathlib import Path

def read_jsonl_file(filepath):
    """Read JSONL file and return list of entries"""
    entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

def write_jsonl_file(filepath, entries):
    """Write entries to JSONL file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

def extract_custom_ids_from_claude():
    """Extract custom_ids from Claude base case files"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    custom_ids = []
    
    claude_files = [
        results_dir / 'claude/Base Case/with_immoralAction_moralConsequence_base_claude.jsonl'
    ]
    
    for filepath in claude_files:
        if filepath.exists():
            entries = read_jsonl_file(filepath)
            for entry in entries:
                custom_id = entry.get('custom_id')
                if custom_id:
                    custom_ids.append(custom_id)
        else:
            print(f"Warning: Claude file not found - {filepath}")
    
    print(f"Extracted {len(custom_ids)} custom_ids from Claude files")
    return custom_ids

def update_custom_ids_in_gpt_files(custom_ids):
    """Update custom_ids in all GPT JSONL files"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    gpt_base_dir = results_dir / 'GPT'
    
    if not gpt_base_dir.exists():
        print(f"Error: GPT directory not found - {gpt_base_dir}")
        return
    
    # Find all JSONL files in GPT directory and subdirectories
    jsonl_files = list(gpt_base_dir.rglob('*.jsonl'))
    
    # Exclude backup files
    jsonl_files = [f for f in jsonl_files if not f.name.endswith('.backup')]
    
    print(f"\nFound {len(jsonl_files)} JSONL files in GPT directory")
    print("="*60)
    
    for jsonl_file in jsonl_files:
        print(f"\nProcessing: {jsonl_file.relative_to(results_dir)}")
        
        # Read existing entries
        entries = read_jsonl_file(jsonl_file)
        
        if len(entries) == 0:
            print(f"  Skipping empty file")
            continue
        
        if len(entries) > len(custom_ids):
            print(f"  Warning: File has {len(entries)} entries but only {len(custom_ids)} custom_ids available")
            print(f"  Will use available custom_ids")
        
        # Update custom_ids in entries
        updated_entries = []
        for i, entry in enumerate(entries):
            if i < len(custom_ids):
                # Update or add custom_id
                entry['custom_id'] = custom_ids[i]
                updated_entries.append(entry)
            else:
                print(f"  Warning: Not enough custom_ids for entry {i}")
                updated_entries.append(entry)
        
        # Create backup (only if it doesn't exist already)
        backup_file = jsonl_file.with_suffix('.jsonl.backup')
        if not backup_file.exists():
            print(f"  Creating backup: {backup_file.name}")
            # Read original again to ensure clean backup
            original_entries = read_jsonl_file(jsonl_file)
            write_jsonl_file(backup_file, original_entries)
        else:
            print(f"  Backup already exists: {backup_file.name}")
        
        # Write updated entries
        write_jsonl_file(jsonl_file, updated_entries)
        print(f"  ✓ Updated custom_ids for {len(updated_entries)} entries")
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"Processed {len(jsonl_files)} files")
    print("Backup files created with .jsonl.backup extension")

def show_sample_updates():
    """Show sample of what will be updated"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    results_dir = project_root / 'results'
    
    # Get one sample GPT file
    gpt_base_dir = results_dir / 'GPT'
    jsonl_files = list(gpt_base_dir.rglob('*.jsonl'))
    jsonl_files = [f for f in jsonl_files if not f.name.endswith('.backup')]
    
    if jsonl_files:
        sample_file = jsonl_files[0]
        print(f"\nSample from: {sample_file.relative_to(results_dir)}")
        entries = read_jsonl_file(sample_file)
        if entries:
            print("\nBEFORE:")
            print(f"custom_id: {entries[0].get('custom_id', 'NOT FOUND')}")
            
    # Get Claude custom_ids
    custom_ids = extract_custom_ids_from_claude()
    if custom_ids:
        print("\nAFTER (will be):")
        print(f"custom_id: {custom_ids[0]}")

def main():
    print("="*60)
    print("UPDATING CUSTOM IDs IN GPT FILES")
    print("="*60)
    
    # Show what will be updated
    print("\n--- Sample Preview ---")
    show_sample_updates()
    
    print("\n" + "="*60)
    print("This will:")
    print("1. Extract custom_ids from Claude base case files")
    print("2. Update custom_ids in ALL GPT JSONL files")
    print("3. Create backups before modifying (if not exists)")
    print("="*60)
    
    response = input("\nProceed with update? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Operation cancelled.")
        return
    
    # Step 1: Extract custom_ids from Claude
    print("\nStep 1: Extracting custom_ids from Claude base case files...")
    custom_ids = extract_custom_ids_from_claude()
    
    if not custom_ids:
        print("Error: No custom_ids found in Claude files!")
        return
    
    # Step 2: Update custom_ids in GPT files
    print("\nStep 2: Updating custom_ids in GPT files...")
    update_custom_ids_in_gpt_files(custom_ids)
    
    print("\n✓ Process completed successfully!")

if __name__ == "__main__":
    main()