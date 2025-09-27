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
    x_ticks = [f'{i}/{len(difficulty)}' for i in range(len(difficulty))]
    plt.plot(x_ticks, difficulty, marker='o')
    # add value per point on the plot
    for i in range(len(difficulty)): plt.text(x_ticks[i], difficulty[i], f'{difficulty[i]}', ha='center', va='bottom')
    plt.xlabel("Difficulty/n_runs")
    plt.ylabel("Number of tasks")
    plt.title("Difficulty Plot")
    plt.savefig(os.path.join(results_dir, "difficulty_plot.png"))
    print(f"Saved plot to {os.path.join(results_dir, 'difficulty_plot.png')}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python split_difficulty_plot_generation.py <results_dir>")
        sys.exit(1)

    results_dir = sys.argv[1]
    # check if file is json or a directory
    files = sorted(os.listdir(results_dir))
    runs = []
    for file in files:
        if file.endswith('.json'):
            data = load_data(os.path.join(results_dir, file))
            runs.append(data)
    task_wise_difficulty = calculate_difficulty(runs)
    # reduce the task_wise_difficulty to a list of length n_runs
    difficulty = reduce_task_wise_difficulty(task_wise_difficulty, len(runs))
    plot_difficulty(difficulty, results_dir)


if __name__ == "__main__":
    main()