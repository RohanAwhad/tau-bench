#!/usr/bin/env python3
"""
Script to calculate pass^k metrics from JSON files containing task results.

Usage: python calculate_pass_k.py <directory_path>

Each JSON file should contain a list of dictionaries with 'task_id' and 'reward' keys.
The script calculates pass^k for k=1 to 5, where pass^k for a task is 1 if all
first k files have reward==1 for that task, otherwise 0.
"""

import json
import os
import sys
import argparse
from collections import defaultdict
from typing import List, Dict, Any


def load_json_files(dir_path: str) -> List[List[Dict[str, Any]]]:
    """
    Load all JSON files from directory in ascending order.

    Args:
        dir_path: Path to directory containing JSON files

    Returns:
        List of data from each JSON file (each file contains list of dicts)

    Raises:
        SystemExit: If directory doesn't exist or no JSON files found
    """
    if not os.path.isdir(dir_path):
        print(f"Error: Directory {dir_path} does not exist")
        sys.exit(1)

    # Get all JSON files and sort them in ascending order
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]

    if not json_files:
        print(f"Error: No JSON files found in directory {dir_path}")
        sys.exit(1)

    json_files.sort()
    print(f"Found {len(json_files)} JSON files: {json_files}")

    # Load each JSON file
    all_data = []
    for filename in json_files:
        filepath = os.path.join(dir_path, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"Error: {filename} should contain a list of dictionaries")
                sys.exit(1)

            all_data.append(data)
            print(f"Loaded {filename}: {len(data)} tasks")

        except FileNotFoundError:
            print(f"Error: File {filepath} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file {filename}: {e}")
            sys.exit(1)

    return all_data


def organize_by_task_id(all_data: List[List[Dict[str, Any]]]) -> Dict[str, List[int]]:
    """
    Organize data by task_id across all files.

    Args:
        all_data: List of data from each JSON file

    Returns:
        Dictionary mapping task_id to list of rewards (one per file, in order)

    Raises:
        SystemExit: If required keys are missing
    """
    # For each task_id seen across all files, record its reward for this file
    # If a task_id doesn't appear in this file, we'll treat it as reward=0
    all_task_ids = set()
    for data in all_data:
        for task in data:
            all_task_ids.add(task['task_id'])

    task_rewards = defaultdict(list)
    for file_idx, file_data in enumerate(all_data):
        # Create a mapping of task_id to reward for this file
        file_task_rewards = {}

        for task in file_data:
            if 'task_id' not in task:
                print(f"Error: Missing 'task_id' key in file {file_idx + 1}")
                sys.exit(1)
            if 'reward' not in task:
                print(f"Error: Missing 'reward' key in file {file_idx + 1}, task {task.get('task_id', 'unknown')}")
                sys.exit(1)

            task_id = task['task_id']
            reward = task['reward']
            file_task_rewards[task_id] = reward

        for task_id in all_task_ids:
            if len(task_rewards[task_id]) == file_idx:  # Only add if we haven't added for this file yet
                reward = file_task_rewards.get(task_id, 0)  # Default to 0 if task not in this file
                task_rewards[task_id].append(reward)

    return dict(task_rewards)


def calculate_pass_k(task_rewards: Dict[str, List[int]], k: int) -> float:
    """
    Calculate pass^k metric.

    Args:
        task_rewards: Dictionary mapping task_id to list of rewards
        k: The k value for pass^k (number of files to consider)

    Returns:
        pass^k value (proportion of tasks that have all first k rewards == 1)
    """
    if k <= 0:
        return 0.0

    total_tasks = len(task_rewards)
    if total_tasks == 0:
        return 0.0

    passed_tasks = 0

    for task_id, rewards in task_rewards.items():
        # Consider only the first k rewards
        first_k_rewards = rewards[:k]

        # Skip if we don't have k files worth of data for this task
        if len(first_k_rewards) < k:
            continue

        # pass^k = 1 if all first k rewards are 1, else 0
        if all(reward == 1 for reward in first_k_rewards):
            passed_tasks += 1

    return passed_tasks / total_tasks


def main():
    """Main function to handle CLI and orchestrate the calculation."""
    parser = argparse.ArgumentParser(
        description="Calculate pass^k metrics from JSON files containing task results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "dir_path",
        help="Path to directory containing JSON files"
    )

    args = parser.parse_args()

    # Load and process JSON files
    print(f"Processing directory: {args.dir_path}")
    all_data = load_json_files(args.dir_path)

    # Organize data by task_id
    task_rewards = organize_by_task_id(all_data)

    print(f"\nFound {len(task_rewards)} unique task IDs")
    print(f"Each task has results from {len(all_data)} files")

    # Calculate and print pass^k for k=1 to 5
    print("\nPass^k Results:")
    print("=" * 40)

    max_k = min(5, len(all_data))  # Don't calculate beyond available files

    for k in range(1, max_k + 1):
        pass_k = calculate_pass_k(task_rewards, k)
        print(f"pass^{k}: {pass_k:.4f}")

    if len(all_data) < 5:
        print(f"\nNote: Only {len(all_data)} files available, so pass^k calculated for k=1 to {len(all_data)}")


if __name__ == "__main__":
    main()
