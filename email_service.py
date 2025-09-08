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

def send_invitation_email(self, to_email, personal_message="", invitation_link=""):
        """Send invitation email to new user"""
        try:
            subject = "You're invited to join dotmobile GORSE Beta!"

            # Create invitation link if not provided
            if not invitation_link:
                invitation_link = f"https://gorse.dotmobile.app/signup?invite={to_email}"

            # Email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #0066ff;">Welcome to dotmobile GORSE Beta!</h2>

                <p>You've been invited to join our exclusive beta program for global connectivity.</p>

                {f'<p><strong>Personal message:</strong> {personal_message}</p>' if personal_message else ''}

                <p>dotmobile V3 "GORSE" provides:</p>
                <ul>
                    <li>Global data connectivity in 160+ countries</li>
                    <li>eSIM technology for instant activation</li>
                    <li>Canadian Full MVNO service (Network 302 100)</li>
                    <li>Beta access to upcoming features</li>
                </ul>

                <p style="margin: 30px 0;">
                    <a href="{invitation_link}" 
                       style="background: #0066ff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Join Beta Program
                    </a>
                </p>

                <p>This invitation expires in 7 days.</p>

                <p>Best regards,<br>The dotmobile Team</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Data On Tap Inc. - Licensed Full MVNO<br>
                    Network 302 100, Parkdale, ON, Canada
                </p>
            </body>
            </html>
            """

            # Send email
            response = self.resend_client.emails.send({
                "from": "noreply@dotmobile.app",
                "to": [to_email],
                "subject": subject,
                "html": body
            })

            print(f"Invitation email sent to {to_email}: {response}")
            return True

        except Exception as e:
            print(f"Error sending invitation email: {str(e)}")
            return False

def send_esim_ready_email(self, to_email, plan_details):
        """Send eSIM ready notification email"""
        try:
            subject = "🎉 Your dotmobile Beta eSIM is Ready!"

            # Email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #0066ff;">Your Beta eSIM is Ready! 🎉</h2>

                <p>Great news! Your payment has been processed and your beta eSIM is now ready for download.</p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #0066ff; margin-top: 0;">Your Beta Plan Details:</h3>
                    <ul>
                        <li><strong>Data Allowance:</strong> 1000MB (1GB)</li>
                        <li><strong>Validity:</strong> 10 days</li>
                        <li><strong>Coverage:</strong> Global (160+ countries)</li>
                        <li><strong>Plan Type:</strong> OXIO 10-day Demo</li>
                    </ul>
                </div>

                <p style="margin: 30px 0;">
                    <a href="https://gorse.dotmobile.app/dashboard" 
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Download Your eSIM
                    </a>
                </p>

                <h3>What's Next?</h3>
                <ol>
                    <li>Visit your dashboard to download the eSIM profile</li>
                    <li>Follow the setup instructions for your device</li>
                    <li>Start using global connectivity immediately</li>
                    <li>Provide feedback to help us improve the service</li>
                </ol>

                <p><strong>Note:</strong> Your 1000MB data bonus has been added to your account and is ready to use!</p>

                <p>Welcome to the future of global connectivity!</p>

                <p>Best regards,<br>The dotmobile Team</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Data On Tap Inc. - Licensed Full MVNO<br>
                    Network 302 100, Parkdale, ON, Canada<br>
                    Need help? Contact us at support@dotmobile.app
                </p>
            </body>
            </html>
            """

            # Send email
            response = self.resend_client.emails.send({
                "from": "noreply@dotmobile.app",
                "to": [to_email],
                "subject": subject,
                "html": body
            })

            print(f"eSIM ready email sent to {to_email}: {response}")
            return True

        except Exception as e:
            print(f"Error sending eSIM ready email: {str(e)}")
            return False