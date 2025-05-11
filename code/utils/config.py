import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rel_path(*path):
    # Go from utils → code → project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(project_root, *path)


# Prompt Files
PROMPT_FILES = {
    # Choice of Action
    "choice_with_norm": rel_path("data", "prompts", "choice_prompts_with_norm.jsonl"),
    "choice_without_norm": rel_path("data", "prompts", "choice_prompts_without_norm.jsonl"),

    # Immoral Action Justification
    "immoral_with_norm": rel_path("data", "prompts", "immoral_act_with_norm_prompts.jsonl"),
    "immoral_without_norm": rel_path("data", "prompts", "immoral_act_without_norm_prompts.jsonl"),

    # Intention vs. Outcome
    "moral_action_immoral_outcome": rel_path("data", "prompts", "with_moralAction_immoralConsequnece_prompts.jsonl"),
    "immoral_action_moral_outcome": rel_path("data", "prompts", "with_immoralAction_moralConsequnece_prompts.jsonl"),

    # Prompt Injection (4 sets)
    "injection_moral_action_immoral_outcome": rel_path("data", "prompts", "injection_moralAction_immoralOutcome_prompts.jsonl"),
    "pro_action_immoral": rel_path("data", "prompts", "anti_action_immoralAction_prompts.jsonl"),
    "pro_outcome_immoral": rel_path("data", "prompts", "pro_outcome_immoralAction_prompts.jsonl"),
    "outcome_weighted_moral": rel_path("data", "prompts", "outcome_weighted_moralAction_prompts.jsonl"),
}

# Output directory for batch files
BATCH_DIR = rel_path("data", "batch")
if not os.path.exists(BATCH_DIR):
    os.makedirs(BATCH_DIR)
