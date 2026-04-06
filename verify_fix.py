import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'server'))

from server.my_env_environment import MyEnvironment
from models import MyAction

def test_reward_logic():
    env = MyEnvironment()
    obs = env.reset()
    print(f"Initial Email: {obs.email}")

    # The actual label should be in obs.info['correct'] or similar? 
    # Let's find what it is from the data
    from email_loader import get_emails
    emails = get_emails()
    correct_label = next(e['label'] for e in emails if e['text'] == obs.email)
    
    print(f"Taking correct action: {correct_label}")
    action = MyAction(action_type=correct_label)
    new_obs = env.step(action)
    
    print(f"Reward: {new_obs.reward}")
    print(f"Info: {new_obs.info}")
    
    # Check if reward is > 0
    assert new_obs.reward > 0, f"Expected positive reward for correct action, got {new_obs.reward}"
    print("✅ TEST PASSED: Reward is positive for correct action.")

    # Now verify state persistence (simulate multiple steps)
    # If the state was being lost, step_count or email matching would fail.
    assert env.state.streak == 1, "Streak should have incremented"
    print("✅ TEST PASSED: State persistence (streak) confirmed.")

if __name__ == "__main__":
    try:
        test_reward_logic()
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
