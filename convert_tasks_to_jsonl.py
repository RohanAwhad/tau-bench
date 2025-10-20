#!/usr/bin/env python3
"""Convert airline tasks_test.py to CSV format."""

import json
import sys
from pathlib import Path
import pandas as pd

# Add the project root to the path so we can import tau_bench
sys.path.insert(0, str(Path(__file__).parent))

from tau_bench.envs.airline.tasks_test import TASKS


def main():
    output_file = Path(__file__).parent / "airline_tasks_test.csv"

    print(f"Converting {len(TASKS)} tasks to CSV format...")

    # Convert all tasks to a list of dictionaries
    data = []
    for i, task in enumerate(TASKS):
        data.append({
            "task_id": i,
            "user_id": task.user_id,
            "instruction": task.instruction,
            "num_actions": len(task.actions),
            "actions": json.dumps([
                {
                    "name": action.name,
                    "kwargs": action.kwargs
                }
                for action in task.actions
            ], ensure_ascii=False),
            "outputs": json.dumps(task.outputs, ensure_ascii=False)
        })

    # Create DataFrame and save to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✓ Successfully wrote {len(TASKS)} tasks to {output_file}")

    # Print some statistics
    print(f"\nStatistics:")
    print(f"  Total tasks: {len(TASKS)}")
    print(f"  Unique users: {len(set(task.user_id for task in TASKS))}")
    print(f"  Tasks with actions: {sum(1 for task in TASKS if task.actions)}")
    print(f"  Tasks with outputs: {sum(1 for task in TASKS if task.outputs)}")

    # Show a sample
    print(f"\nSample (first 3 rows):")
    print(df[['task_id', 'user_id', 'num_actions']].head(3).to_string(index=False))


if __name__ == "__main__":
    main()
