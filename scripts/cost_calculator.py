from dataclasses import dataclass
import json
import sys
import argparse
import os

parser = argparse.ArgumentParser()

# Create mutually exclusive group for file/directory input
input_group = parser.add_mutually_exclusive_group(required=True)
input_group.add_argument("--json_file", type=str, help="Path to a single JSON file to process")
input_group.add_argument("--json_dir", type=str, help="Path to directory containing JSON files to process")

parser.add_argument('--api_model', type=str, required=True)
parser.add_argument('--refiner_model', type=str, required=False)
parser.add_argument('--judge_model', type=str, required=False)
args = parser.parse_args()

# Cost per token for each model
@dataclass
class ModelCost:
    input_token_price: float
    output_token_price: float

MODEL_COST_MAP = {
    'gpt-4.1-mini': ModelCost(input_token_price=0.4/1e6, output_token_price=1.6/1e6),
    'gpt-5-nano': ModelCost(input_token_price=0.05/1e6, output_token_price=0.4/1e6),
}

# ===

def find_json_files(directory_path):
    """Find all JSON files in the specified directory."""
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    try:
        all_files = os.listdir(directory_path)
        json_files = [f for f in all_files if f.lower().endswith('.json')]

        if not json_files:
            print(f"Warning: No JSON files found in directory '{directory_path}'.", file=sys.stderr)
            return []

        # Return full paths, sorted alphabetically
        json_files.sort()
        return [os.path.join(directory_path, f) for f in json_files]

    except PermissionError:
        print(f"Error: Permission denied accessing directory '{directory_path}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read directory '{directory_path}': {e}", file=sys.stderr)
        sys.exit(1)

def process_single_file(file_path):
    """Process a single JSON file and return its total cost."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Calculate total cost for all objects in the file
        total_cost = 0
        for obj in data:
            total_cost += calculate_cost(obj)
        return total_cost
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{file_path}': {e}", file=sys.stderr)
        return None
    except PermissionError:
        print(f"Error: Permission denied reading file '{file_path}'.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: Failed to process file '{file_path}': {e}", file=sys.stderr)
        return None

def calculate_cost_for_turn(turn: dict):
    if args.api_model:
        primary_response_usage = turn['metadata']['primary_response']['usage']
        primary_response_cost = primary_response_usage['prompt_tokens'] * MODEL_COST_MAP[args.api_model].input_token_price + primary_response_usage['completion_tokens'] * MODEL_COST_MAP[args.api_model].output_token_price
    else:
        primary_response_cost = 0

    if args.refiner_model:
        refiner_response_usage = turn['metadata']['refiner_usage']
        refiner_response_cost = refiner_response_usage['prompt_tokens'] * MODEL_COST_MAP[args.refiner_model].input_token_price + refiner_response_usage['completion_tokens'] * MODEL_COST_MAP[args.refiner_model].output_token_price
    else:
        refiner_response_cost = 0

    if args.judge_model:
        judge_response_usage = turn['metadata']['refiner_usage']['judge_usage']
        judge_response_cost = judge_response_usage['prompt_tokens'] * MODEL_COST_MAP[args.judge_model].input_token_price + judge_response_usage['completion_tokens'] * MODEL_COST_MAP[args.judge_model].output_token_price
    else:
        judge_response_cost = 0

    return primary_response_cost + refiner_response_cost + judge_response_cost

def calculate_cost(obj: dict):
    traj = obj['traj']
    total_cost = 0
    for turn in traj:
        if turn['role'] == 'assistant':
            total_cost += calculate_cost_for_turn(turn)
    return total_cost

# Main execution logic
if args.json_file:
    # Single file mode - maintain backward compatibility
    cost = process_single_file(args.json_file)
    if cost is not None:
        print(cost)
    else:
        sys.exit(1)
elif args.json_dir:
    # Directory mode - process all JSON files
    json_files = find_json_files(args.json_dir)
    if not json_files:
        sys.exit(1)

    # Process all files and collect results
    file_costs = []
    total_cost = 0
    failed_files = 0

    for file_path in json_files:
        cost = process_single_file(file_path)
        if cost is not None:
            filename = os.path.basename(file_path)
            file_costs.append((filename, cost))
            total_cost += cost
        else:
            failed_files += 1

    # Output results (will be enhanced in next step)
    print("Cost Analysis Results:")
    print("=" * 22)
    for filename, cost in file_costs:
        print(f"{filename}: ${cost:.6f}")
    print("=" * 22)
    print(f"Total cost: ${total_cost:.6f}")

    if failed_files > 0:
        print(f"\nWarning: {failed_files} files failed to process.", file=sys.stderr)