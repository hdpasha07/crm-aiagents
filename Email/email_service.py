def send_email(to_email, subject, body):
    print(f"\n{'='*50}")
    print(f"📧 DRAFT EMAIL TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print(f"BODY:\n{body}")
    print(f"{'='*50}\n")
    return True

def send_complaint_email(to_email, subject, body):
    return send_email(to_email, subject, body)
