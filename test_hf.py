import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'server'))

from client import MyEnv

def test_hf_live():
    # Connect to the live deployed server
    base_url = "https://pritoo-my-openenv-email-env.hf.space"
    print(f"Connecting to live server at {base_url}...")
    
    with MyEnv(base_url=base_url).sync() as client:
        # Reset the environment (starts a session)
        state_result = client.reset()
        email_text = state_result.observation.email
        print(f"Loaded Email: '{email_text}'")
        
        # Figure out the expected label by doing basic keyword checking
        # to guarantee a correct answer for our test.
        # Alternatively, we can let our client's built in act() handle it.
        action = client.act(state_result)
        print(f"Submitting Action: '{action.action_type}'")
        
        # Step the environment
        step_result = client.step(action)
        reward = step_result.reward
        print(f"Result Reward: {reward}")
        
        if reward > 0:
            print("✅ Live test SUCCESSFUL. Reward is positive.")
        else:
            print("❌ Live test FAILED. Reward is not positive.")

if __name__ == "__main__":
    test_hf_live()
