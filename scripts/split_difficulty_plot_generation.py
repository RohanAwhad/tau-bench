import json
import os
import sys
import matplotlib.pyplot as plt

def load_data(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {json_file}")
        sys.exit(1)

    return data

def calculate_difficulty(runs: list[list[dict]]) -> list[int]:
    """
    Every run has a list of dict.
    Each dict has a task_id and a reward field.
    We want to calculate the difficulty of the task.
    Difficulty is basically how many times the reward is 1 for each task.
    Returns a list of len(tasks)
    """
    ret = {} # task_id -> count_of_1s
    for run in runs:
        for task in run:
            if task['task_id'] not in ret:
                ret[task['task_id']] = 0
            if task['reward'] == 1:
                ret[task['task_id']] += 1
    return list(ret.values())


def reduce_task_wise_difficulty(task_wise_difficulty: list[int], n_runs: int) -> list[int]:
    """
    Reduce the task-wise difficulty to a list of length n_runs+1 (0 to n_runs)
    """
    ret = [0] * (n_runs + 1)
    for x in task_wise_difficulty:
        ret[x] += 1
    return ret


def plot_difficulty(difficulty: list[int], results_dir: str):
    """
    Line Plot the difficulty of the task.
    n_runs is the number of runs
    x-axis: difficulty/n_runs
    y-axis: number of tasks

    Saves the plot to a file called difficulty_plot.png in results_dir
    """
    x_ticks = [f'{i}/{len(difficulty)-1}' for i in range(len(difficulty))]
    plt.plot(x_ticks, difficulty, marker='o')
    # add value per point on the plot
    for i in range(len(difficulty)): plt.text(x_ticks[i], difficulty[i], f'{difficulty[i]}', ha='center', va='bottom')
    plt.xlabel("Difficulty/n_runs")
    plt.ylabel("Number of tasks")
    plt.title("Difficulty Plot")
    plt.savefig(os.path.join(results_dir, "difficulty_plot.png"))
    print(f"Saved plot to {os.path.join(results_dir, 'difficulty_plot.png')}")


def plot_multiple_difficulties(difficulties_by_dir: dict[str, list[int]], output_path: str):
    """
    Plot multiple difficulty distributions in a single figure.

    Args:
        difficulties_by_dir: dict mapping directory names to their difficulty distributions
        output_path: path where to save the plot
    """
    plt.figure(figsize=(12, 6))

    for dir_name, difficulty in difficulties_by_dir.items():
        x_ticks = list(range(len(difficulty)))
        plt.plot(x_ticks, difficulty, marker='o', label=os.path.basename(dir_name))

    plt.xlabel("Difficulty (number of successful runs)")
    plt.ylabel("Number of tasks")
    plt.title("Difficulty Distribution Comparison")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path)
    print(f"Saved plot to {output_path}")


def process_directory(results_dir: str) -> tuple[list[int], int]:
    """
    Process a single directory and return its difficulty distribution and number of runs.

    Returns:
        tuple of (difficulty distribution, number of runs)
    """
    files = sorted(os.listdir(results_dir))
    runs = []
    for file in files:
        if file.endswith('.json'):
            data = load_data(os.path.join(results_dir, file))
            runs.append(data)

    if not runs:
        print(f"Warning: No JSON files found in {results_dir}")
        return [], 0

    task_wise_difficulty = calculate_difficulty(runs)
    difficulty = reduce_task_wise_difficulty(task_wise_difficulty, len(runs))
    return difficulty, len(runs)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single directory: python split_difficulty_plot_generation.py <results_dir>")
        print("  Multiple directories: python split_difficulty_plot_generation.py <dir1> <dir2> ... <dirN> <output_path>")
        sys.exit(1)

    # Single directory mode
    if len(sys.argv) == 2:
        results_dir = sys.argv[1]
        difficulty, n_runs = process_directory(results_dir)
        if difficulty:
            plot_difficulty(difficulty, results_dir)

    # Multiple directory mode
    else:
        directories = sys.argv[1:-1]
        output_path = sys.argv[-1]

        # Validate that output_path looks like a file path
        if not output_path.endswith('.png'):
            print("Error: Last argument should be the output path (must end with .png)")
            print("Usage: python split_difficulty_plot_generation.py <dir1> <dir2> ... <dirN> <output_path>")
            sys.exit(1)

        difficulties_by_dir = {}
        for directory in directories:
            if not os.path.isdir(directory):
                print(f"Error: {directory} is not a valid directory")
                sys.exit(1)

            difficulty, n_runs = process_directory(directory)
            if difficulty:
                difficulties_by_dir[directory] = difficulty

        if not difficulties_by_dir:
            print("Error: No valid data found in any directory")
            sys.exit(1)

        plot_multiple_difficulties(difficulties_by_dir, output_path)


if __name__ == "__main__":
    main()