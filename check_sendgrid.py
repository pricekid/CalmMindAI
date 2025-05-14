"""
Check if SendGrid is properly importable.
"""
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    print("SUCCESS: SendGrid and its helpers can be imported")
except ImportError as e:
    print(f"FAILED: {str(e)}")