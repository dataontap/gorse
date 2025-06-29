
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send an email using SMTP configuration from environment variables
    Returns True if successful, False otherwise
    """
    try:
        # Get SMTP configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        from_email = os.environ.get('FROM_EMAIL', smtp_username)
        
        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured in environment variables")
            print("Required: SMTP_USERNAME, SMTP_PASSWORD")
            print("Optional: SMTP_SERVER (default: smtp.gmail.com), SMTP_PORT (default: 587), FROM_EMAIL")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Add text body
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML body if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Connect to server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_test_email(to_email: str = "aa@dotmobile.app") -> bool:
    """Send a test email to verify email functionality"""
    subject = "Test Email from GORSE System"
    body = """
    This is a test email to verify that the email system is working correctly.
    
    If you receive this email, the Firebase authentication email sending is functional.
    
    Best regards,
    GORSE System
    """
    
    html_body = """
    <html>
        <body>
            <h2>Test Email from GORSE System</h2>
            <p>This is a test email to verify that the email system is working correctly.</p>
            <p>If you receive this email, the Firebase authentication email sending is functional.</p>
            <br>
            <p>Best regards,<br>
            <strong>GORSE System</strong></p>
        </body>
    </html>
    """
    
    return send_email(to_email, subject, body, html_body)
