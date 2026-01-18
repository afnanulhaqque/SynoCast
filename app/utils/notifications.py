
import os
import requests
import logging

import json
import logging
from google import genai
from flask import render_template_string, current_app

logger = logging.getLogger(__name__)

def is_alert_relevant(alert, prefs):
    """
    Determines if an alert matches the user's preferences.
    """
    if not prefs:
        return True # Default to all if no prefs
        
    event = alert.get('event', '').lower()
    desc = alert.get('description', '').lower()
    
    # Check severity
    # OpenWeather alerts doesn't always have standard severity field, often it's in description or tags
    # We'll assume 'severity' key exists or infer from event name
    # For now, simplistic matching
    
    pref_types = prefs.get('types', [])
    if not pref_types: return True
    
    relevant = False
    if 'severe' in pref_types:
        if any(x in event for x in ['severe', 'storm', 'tornado', 'hurricane', 'warning']):
            relevant = True
    if 'rain' in pref_types:
        if any(x in event for x in ['rain', 'flood', 'shower']):
            relevant = True
    if 'temp' in pref_types:
        if any(x in event for x in ['heat', 'cold', 'freeze', 'chill']):
            relevant = True
    if 'air' in pref_types:
        if any(x in event for x in ['quality', 'pollution', 'smoke', 'dust']):
            relevant = True
            
    return relevant

def get_ai_advice(alert):
    """
    Uses Gemini to generate safety advice for the alert.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Stay safe and follow local authority guidelines."
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Provide concise, actionable safety advice (max 3 sentences) for this weather alert:
        Event: {alert.get('event')}
        Description: {alert.get('description')}
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI advice error: {e}")
        return "Stay indoors and monitor local news."


def send_email(to_email, subject, text_content=None, html_content=None):
    """
    Sends an email using the Resend API.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev") # Default Resend testing email
    
    if not api_key:
        logger.warning(f"RESEND_API_KEY not set. Email to {to_email} suppressed.")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {text_content}")
        return False

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": "SynoCast <" + sender_email + ">",
        "to": [to_email],
        "subject": subject,
        "text": text_content or "",
        "html": html_content or text_content or ""
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.ok:
            return True
        else:
            logger.error(f"Resend API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_otp_email(to_email, otp):
    """
    Sends a verification OTP email.
    """
    subject = f"{otp} is your SynoCast verification code"
    
    text_body = f"""
    Welcome to SynoCast!
    
    Your verification code is: {otp}
    
    This code will expire in 10 minutes.
    If you did not request this, please ignore this email.
    """
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #3f5e96; text-align: center;">SynoCast Verification</h2>
        <p style="text-align: center; font-size: 16px; color: #555;">Use the code below to complete your subscription:</p>
        <div style="background-color: #f0f4f8; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
            <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #141e30;">{otp}</span>
        </div>
        <p style="font-size: 14px; color: #777; text-align: center;">This code will expire in 10 minutes.</p>
    </div>
    """
    
    return send_email(to_email, subject, text_body, html_body)

def send_alert_email(to_email, alert, advice):
    """
    Sends a weather alert email with an unsubscribe link.
    """
    subject = f"⚠️ Alert: {alert.get('event', 'Weather Alert')}"
    
    severity = alert.get('severity', 'Unknown')
    description = alert.get('description', 'No details available.')
    
    # Generate Unsubscribe Link
    # Ideally, this should be a signed URL or have a token, but for now we'll point to the page
    # In a real app, generate a unique token for the user.
    unsub_url = f"https://syno-cast.vercel.app/unsubscribe?email={to_email}"
    
    text_body = f"""
    SynoCast Weather Alert
    
    Event: {alert.get('event')}
    Severity: {severity}
    
    {description}
    
    AI Advice:
    {advice}
    
    Stay safe!
    
    To unsubscribe, visit: {unsub_url}
    """
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border-left: 5px solid #ff4444;">
        <h2 style="color: #d32f2f;">{alert.get('event')}</h2>
        <p><strong>Severity:</strong> {severity}</p>
        <p style="background-color: #fff3f3; padding: 10px; border-radius: 4px;">{description}</p>
        
        <h3 style="color: #3f5e96;">AI Safety Advice</h3>
        <p>{advice}</p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #888; text-align: center;">
            <a href="{unsub_url}" style="color: #888;">Unsubscribe from alerts</a>
        </p>
    </div>
    """
    
    return send_email(to_email, subject, text_body, html_body)

