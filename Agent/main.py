from .graph import build_graph

if __name__ == "__main__":
    app = build_graph()

    complaint = {
        "complaint_text": "My recent order is marked as delivered, but I have not received it. I contacted support earlier and have not received an update. Please investigate the delivery status and let me know the next steps."
    }

    result = app.invoke(complaint)

    print("\nFINAL STATE\n")
    for k, v in result.items():
        print(f"{k}: {v}")
