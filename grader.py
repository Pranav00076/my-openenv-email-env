def grade_episode(history):
    total_reward = sum(obs.reward for _, obs in history)

    correct = sum(1 for _, obs in history if obs.info.get("is_correct", False))

    accuracy = correct / len(history) if history else 0

    avg_reward = total_reward / len(history) if history else 0

    raw_score = (0.7 * accuracy) + (0.3 * avg_reward)
    score = max(0.0, min(1.0, raw_score))  # clamp to [0.0, 1.0]

    return {
        "total_reward": total_reward,
        "accuracy": accuracy,
        "avg_reward": avg_reward,
        "score": score,
        "steps": len(history)
    }