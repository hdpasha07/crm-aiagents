from Agent.llm import get_llm

def ping_test():
    print("🔌 Booting up LLM...")
    llm = get_llm()
    
    print("📡 Sending ping to Gemini API...")
    try:
        # We use a tiny prompt to ensure we don't trigger payload size limits
        response = llm.invoke("Reply with exactly one word: 'Connected'.")
        print("✅ SUCCESS! Response received:", response.content)
    except Exception as e:
        print("❌ FAILED! Error:", e)

if __name__ == "__main__":
    ping_test()