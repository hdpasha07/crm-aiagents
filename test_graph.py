from Agent.graph import build_graph # Ensure your import is correct

def run_test():
    agent_app = build_graph()

    initial_state = {
        "user_id": "user_123", 
        "complaint_text": "My server cluster B went down again, this is unacceptable!"
    }
    initial_state = {
        "user_id": "user_123", 
        "complaint_text": "I was charged twice for order #99823, but the order was never created. I need a refund immediately!"
    }

    print("🚀 Starting Graph Execution...\n")
    
    # We use .stream() instead of .invoke() to watch the DAG execute step-by-step
    final_state = None
    for step in agent_app.stream(initial_state):
        for node_name, current_state in step.items():
            print(f"✅ Node Completed: [{node_name}]")
            final_state = current_state  # Update with the latest state

    print("\n🏁 Execution Complete. Checking Injected Memory:")
    print("-" * 40)
    print("User Profile Found:", final_state.get("user_profile"))
    print("Category Assigned:", final_state.get("category"))
    print("Priority Assigned:", final_state.get("priority"))
    print("Response Draft:", final_state.get("response_email"))
    print("-" * 40)

if __name__ == "__main__":
    run_test()