#!/usr/bin/env python3
"""
Gmail Email Configuration Guide
"""

print("🔧 Gmail Email Configuration Guide")
print("=" * 50)

print("""
📧 COMMON GMAIL EMAIL ISSUES AND SOLUTIONS:

❌ ISSUE 1: "Less Secure App Access" Disabled
✅ SOLUTION: 
   1. Go to: https://myaccount.google.com/security
   2. Scroll down to "Less secure app access"
   3. Turn it ON
   4. Wait 5-10 minutes for changes to take effect

❌ ISSUE 2: 2-Factor Authentication Enabled
✅ SOLUTION: Use App Password instead of regular password
   1. Go to: https://myaccount.google.com/apppasswords
   2. Select "Mail" for the app
   3. Select "Other (Custom name)" and enter "State Counter"
   4. Click "Generate"
   5. Copy the 16-character password (without spaces)
   6. Use this as MAIL_PASSWORD in your .env file

❌ ISSUE 3: Gmail Blocking Suspicious Activity
✅ SOLUTION:
   1. Check your Gmail for security alerts
   2. Approve the login attempt if you see one
   3. Add your server IP to trusted locations if possible

❌ ISSUE 4: Incorrect Email Format
✅ SOLUTION: Ensure MAIL_USERNAME is the full email address
   Correct: nikitaprp4@gmail.com
   Incorrect: nikitaprp4

🔍 DEBUGGING STEPS:

1. Check if environment variables are loaded:
   curl https://api.seo.prpwebs.com/debug/email

2. Test email sending locally:
   python test_production_email.py

3. Check server logs for email sending errors

4. Verify the "From" address matches your Gmail account

📋 PRODUCTION CHECKLIST:

□ Gmail "Less Secure App Access" is ON
□ OR using App Password (recommended for 2FA)
□ MAIL_USERNAME is full Gmail address
□ MAIL_PASSWORD is correct (App Password if 2FA)
□ No Gmail security alerts blocking access
□ Server can reach smtp.gmail.com:587

🚀 ALTERNATIVE EMAIL PROVIDERS:

If Gmail continues to have issues, consider:
- SendGrid (more reliable for production)
- AWS SES (Amazon's email service)
- Mailgun (good transactional email)

""")

print("⚠️  SECURITY NOTE:")
print("Never commit real email credentials to Git!")
print("Always use environment variables in production.")
