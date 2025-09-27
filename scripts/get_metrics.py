#!/usr/bin/env python3
import json
import os
import sys

def get_accuracy(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {json_file}")
        sys.exit(1)

    total_tasks = len(data)
    correct_tasks = 0

    for task in data:
        if task.get('reward', 0) == 1:
            correct_tasks += 1

    if total_tasks == 0:
        accuracy = 0.0
    else:
        accuracy = correct_tasks / total_tasks

    return accuracy


def main():
    if len(sys.argv) != 2:
        print("Usage: python get_metrics.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    # check if file is json or a directory
    if os.path.isdir(json_file):
        files = sorted(os.listdir(json_file))
        for file in files:
            if file.endswith('.json'):
                accuracy = get_accuracy(os.path.join(json_file, file))
                print(f"{file} | Accuracy: {accuracy:.4f}")
    else:
        accuracy = get_accuracy(json_file)
        print(f"{json_file} | Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()