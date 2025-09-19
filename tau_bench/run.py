# Copyright Sierra

import os
import json
import random
import traceback
from math import comb
import multiprocessing
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from tau_bench.envs import get_env
from tau_bench.agents.base import Agent
from tau_bench.types import EnvRunResult, RunConfig
from litellm import provider_list
from tau_bench.envs.user import UserStrategy


def run(config: RunConfig) -> List[EnvRunResult]:
    assert config.env in ["retail", "airline"], "Only retail and airline envs are supported"
    assert config.model_provider in provider_list, "Invalid model provider"
    assert config.user_model_provider in provider_list, "Invalid user model provider"
    assert config.agent_strategy in ["tool-calling", "act", "react", "few-shot"], "Invalid agent strategy"
    assert config.task_split in ["train", "test", "dev"], "Invalid task split"
    assert config.user_strategy in [item.value for item in UserStrategy], "Invalid user strategy"

    random.seed(config.seed)
    time_str = datetime.now().strftime("%m%d%H%M%S")
    ckpt_path = f"{config.log_dir}/{config.agent_strategy}-{config.model.split('/')[-1]}-{config.temperature}_range_{config.start_index}-{config.end_index}_user-{config.user_model.split('/')[-1]}-{config.user_strategy}_{time_str}.json"
    os.makedirs(os.path.basename(ckpt_path), exist_ok=True)
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)

    print(f"Loading user with strategy: {config.user_strategy}")
    env = get_env(
        config.env,
        user_strategy=config.user_strategy,
        user_model=config.user_model,
        user_provider=config.user_model_provider,
        task_split=config.task_split,
    )
    agent = agent_factory(
        tools_info=env.tools_info,
        wiki=env.wiki,
        config=config,
    )
    end_index = (
        len(env.tasks) if config.end_index == -1 else min(config.end_index, len(env.tasks))
    )
    results: List[EnvRunResult] = []
    lock = multiprocessing.Lock()
    if config.task_ids and len(config.task_ids) > 0:
        print(f"Running tasks {config.task_ids} (checkpoint path: {ckpt_path})")
    else:
        print(
            f"Running tasks {config.start_index} to {end_index} (checkpoint path: {ckpt_path})"
    )
    for i in range(config.num_trials):
        if config.task_ids and len(config.task_ids) > 0:
            idxs = config.task_ids
        else:
            idxs = list(range(config.start_index, end_index))
        if config.shuffle:
            random.shuffle(idxs)

        def _run(idx: int) -> List[EnvRunResult]:
            print(f"Running task {idx} with best-of-{config.best_of_n}")

            all_results = []
            best_reward = 0.0

            for attempt in range(config.best_of_n):
                isolated_env = get_env(
                    config.env,
                    user_strategy=config.user_strategy,
                    user_model=config.user_model,
                    task_split=config.task_split,
                    user_provider=config.user_model_provider,
                    task_index=idx,
                )

                print(f"  Attempt {attempt + 1}/{config.best_of_n} for task {idx}")
                try:
                    res = agent.solve(
                        env=isolated_env,
                        task_index=idx,
                    )
                    result = EnvRunResult(
                        task_id=idx,
                        reward=res.reward,
                        info={**res.info, "attempt": attempt + 1, "best_of_n": config.best_of_n},
                        traj=res.messages,
                        trial=i,
                    )
                    best_reward = max(best_reward, res.reward)
                except Exception as e:
                    result = EnvRunResult(
                        task_id=idx,
                        reward=0.0,
                        info={"error": str(e), "traceback": traceback.format_exc(), "attempt": attempt + 1, "best_of_n": config.best_of_n},
                        traj=[],
                        trial=i,
                    )

                all_results.append(result)
                print(f"    ✅" if result.reward == 1 else "❌", f"Attempt {attempt + 1} reward: {result.reward}")

            # Set the final reward: 1 if any attempt succeeded, 0 otherwise
            final_reward = 1.0 if best_reward >= 1.0 else 0.0
            print(f"  Final reward for task {idx}: {final_reward} (best attempt: {best_reward})")
            print("-----")

            # Save all results
            with lock:
                data = []
                if os.path.exists(ckpt_path):
                    with open(ckpt_path, "r") as f:
                        data = json.load(f)

                # Add metadata to indicate this is a best-of-n result
                for result in all_results:
                    result.info["final_best_of_n_reward"] = final_reward

                with open(ckpt_path, "w") as f:
                    json.dump(data + [result.model_dump() for result in all_results], f, indent=2)

            return all_results

        with ThreadPoolExecutor(max_workers=config.max_concurrency) as executor:
            res = list(executor.map(_run, idxs))
            # Flatten the list of lists
            for task_results in res:
                results.extend(task_results)

    # Calculate and display best-of-n metrics
    if config.best_of_n > 1:
        display_best_of_n_metrics(results, config.best_of_n)
    else:
        display_metrics(results)

    with open(ckpt_path, "w") as f:
        json.dump([result.model_dump() for result in results], f, indent=2)
        print(f"\n📄 Results saved to {ckpt_path}\n")
    return results


def agent_factory(
    tools_info: List[Dict[str, Any]], wiki, config: RunConfig
) -> Agent:
    if config.agent_strategy == "tool-calling":
        # native tool calling
        from tau_bench.agents.tool_calling_agent import ToolCallingAgent

        return ToolCallingAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=config.model,
            provider=config.model_provider,
            temperature=config.temperature,
        )
    elif config.agent_strategy == "act":
        # `act` from https://arxiv.org/abs/2210.03629
        from tau_bench.agents.chat_react_agent import ChatReActAgent

        return ChatReActAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=config.model,
            provider=config.model_provider,
            use_reasoning=False,
            temperature=config.temperature,
        )
    elif config.agent_strategy == "react":
        # `react` from https://arxiv.org/abs/2210.03629
        from tau_bench.agents.chat_react_agent import ChatReActAgent

        return ChatReActAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=config.model,
            provider=config.model_provider,
            use_reasoning=True,
            temperature=config.temperature,
        )
    elif config.agent_strategy == "few-shot":
        from tau_bench.agents.few_shot_agent import FewShotToolCallingAgent
        assert config.few_shot_displays_path is not None, "Few shot displays path is required for few-shot agent strategy"
        with open(config.few_shot_displays_path, "r") as f:
            few_shot_displays = [json.loads(line)["messages_display"] for line in f]

        return FewShotToolCallingAgent(
            tools_info=tools_info,
            wiki=wiki,
            model=config.model,
            provider=config.model_provider,
            few_shot_displays=few_shot_displays,
            temperature=config.temperature,
        )
    else:
        raise ValueError(f"Unknown agent strategy: {config.agent_strategy}")


def display_best_of_n_metrics(results: List[EnvRunResult], best_of_n: int) -> None:
    def is_successful(reward: float) -> bool:
        return (1 - 1e-6) <= reward <= (1 + 1e-6)

    # Group results by task_id
    task_groups = {}
    for result in results:
        task_id = result.task_id
        if task_id not in task_groups:
            task_groups[task_id] = []
        task_groups[task_id].append(result)

    print(f"🎯 Best-of-{best_of_n} Results:")
    print("=" * 50)

    total_tasks = len(task_groups)
    successful_tasks = 0

    for task_id, task_results in task_groups.items():
        print(f"Task {task_id}:")
        individual_rewards = [r.reward for r in task_results]
        best_reward = max(individual_rewards)
        final_reward = 1.0 if best_reward >= 1.0 else 0.0

        print(f"  Individual attempt rewards: {individual_rewards}")
        print(f"  Best reward: {best_reward}")
        print(f"  Final best-of-{best_of_n} reward: {final_reward}")

        if is_successful(final_reward):
            successful_tasks += 1
            print(f"  ✅ Task {task_id} PASSED")
        else:
            print(f"  ❌ Task {task_id} FAILED")
        print()

    success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0
    print(f"🏆 Overall Success Rate: {successful_tasks}/{total_tasks} = {success_rate:.2%}")
    print(f"📊 Final Score: {success_rate}")


def display_metrics(results: List[EnvRunResult]) -> None:
    def is_successful(reward: float) -> bool:
        return (1 - 1e-6) <= reward <= (1 + 1e-6)

    num_trials = len(set([r.trial for r in results]))
    rewards = [r.reward for r in results]
    avg_reward = sum(rewards) / len(rewards)
    # c from https://arxiv.org/pdf/2406.12045
    c_per_task_id: dict[int, int] = {}
    for result in results:
        if result.task_id not in c_per_task_id:
            c_per_task_id[result.task_id] = 1 if is_successful(result.reward) else 0
        else:
            c_per_task_id[result.task_id] += 1 if is_successful(result.reward) else 0
    pass_hat_ks: dict[int, float] = {}
    for k in range(1, num_trials + 1):
        sum_task_pass_hat_k = 0
        for c in c_per_task_id.values():
            sum_task_pass_hat_k += comb(c, k) / comb(num_trials, k)
        pass_hat_ks[k] = sum_task_pass_hat_k / len(c_per_task_id)
    print(f"🏆 Average reward: {avg_reward}")
    print("📈 Pass^k")
    for k, pass_hat_k in pass_hat_ks.items():
        print(f"  k={k}: {pass_hat_k}")
