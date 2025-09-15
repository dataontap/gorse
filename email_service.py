import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

def send_email_via_resend(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send an email using Resend API - preferred method for reliable delivery
    Returns True if successful, False otherwise
    """
    try:
        import resend
        
        # Get Resend API key from environment
        api_key = os.environ.get('RESEND_API_KEY')
        if not api_key:
            print("RESEND_API_KEY not configured in environment variables")
            return False
            
        resend.api_key = api_key
        
        # Default sender email - now using your verified domain
        from_email = os.environ.get('FROM_EMAIL', 'rbm@dotmobile.app')
        
        # Use HTML body if available, otherwise use plain text
        email_content = html_body if html_body else body
        content_type = 'html' if html_body else 'text'
        
        # Send email via Resend
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
        }
        
        if content_type == 'html':
            params["html"] = email_content
        else:
            params["text"] = email_content
            
        response = resend.Emails.send(params)
        
        # Handle response format - can be dict or object
        email_id = None
        if hasattr(response, 'id'):
            email_id = response.id
        elif isinstance(response, dict) and 'id' in response:
            email_id = response['id']
            
        print(f"Email sent successfully via Resend to {to_email}. ID: {email_id}")
        return True
        
    except ImportError:
        print("Resend library not installed. Install with: pip install resend")
        return False
    except Exception as e:
        print(f"Failed to send email via Resend to {to_email}: {str(e)}")
        return False

def send_email_via_smtp(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send an email using SMTP configuration from environment variables
    DEPRECATED: Use send_email_via_resend() for better deliverability
    Only use this as emergency fallback with Gmail App Password
    """
    try:
        # Get SMTP configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')  # Must be App Password for Gmail
        from_email = os.environ.get('FROM_EMAIL', smtp_username)

        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured in environment variables")
            print("Required: SMTP_USERNAME, SMTP_PASSWORD (use App Password for Gmail)")
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

        print(f"Email sent successfully via SMTP to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email via SMTP to {to_email}: {str(e)}")
        return False

def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send an email using the best available method
    Priority: 1) Resend API, 2) SMTP fallback
    Returns True if successful, False otherwise
    """
    # Try Resend first (preferred method)
    if send_email_via_resend(to_email, subject, body, html_body):
        return True
    
    # Fall back to SMTP if Resend fails
    print("Resend failed, attempting SMTP fallback...")
    return send_email_via_smtp(to_email, subject, body, html_body)

def send_test_email(to_email: str = "aa@dotmobile.app") -> bool:
    """Send a test email to verify email functionality"""
    # Test directly with Resend, bypassing the fallback logic for testing
    return send_email_via_resend(
        to_email=to_email,
        subject="Test Email from DOTM System - Fixed!",
        body="This is a test email to verify that the email system is working correctly.",
        html_body="""
        <html>
            <body>
                <h2>✅ Email System Fixed!</h2>
                <p>This test confirms the DOTM email system is now working with Resend.</p>
                <p>Magic link emails should now be delivered successfully.</p>
                <br>
                <p>Best regards,<br>
                <strong>DOTM Team</strong></p>
            </body>
        </html>
        """
    )

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