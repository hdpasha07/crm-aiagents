from .graph import build_graph

if __name__ == "__main__":
    app = build_graph()

    complaint = {
        "complaint_text": "Hi my name is Shrey Patel and I ordered an iPhone from your store seven days ago and I already made full prepaid payment but your application is showing the order status as delivered even though I never received the product this is my second complaint because I already contacted your support team two days ago and they promised to check the issue but I have not received any response or update yet this situation is extremely frustrating and unacceptable if this issue is not resolved immediately or my money is not refunded I will be forced to file a formal consumer complaint and take legal action against your company"
    }

    result = app.invoke(complaint)

    print("\nFINAL STATE\n")
    for k, v in result.items():
        print(f"{k}: {v}")