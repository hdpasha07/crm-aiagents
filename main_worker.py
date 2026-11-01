from Backend.worker import process_complaints, send_complaint_email

__all__ = ["process_complaints", "send_complaint_email"]

if __name__ == "__main__":
    process_complaints()
