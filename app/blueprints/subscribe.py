
import json
import random
import logging
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, current_app, flash, redirect, url_for
from app.database import get_db
from app import utils
from app.extensions import csrf

subscribe_bp = Blueprint('subscribe', __name__)
logger = logging.getLogger(__name__)

@subscribe_bp.route("/otp", methods=["POST"])
@csrf.exempt
def otp_handler():
    """
    Handles OTP generation (request) and verification.
    """
    # Try to get data from form or JSON
    action = request.form.get('action') 
    if not action:
        json_data = request.get_json(silent=True)
        if json_data:
            action = json_data.get('action')
    
    if action == 'request':
        email = request.form.get('email')
        preferences_raw = request.form.get('preferences')
        
        if not email:
            json_data = request.get_json(silent=True)
            if json_data:
                email = json_data.get('email')
                preferences_raw = json_data.get('preferences')
        
        if not email:
            return jsonify({"success": False, "message": "Email is required."}), 400
            
        # check if already subscribed?
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM subscriptions WHERE email = ?", (email,))
            if c.fetchone():
                return jsonify({"success": False, "message": "This email is already subscribed!"}), 400

        otp = str(random.randint(100000, 999999))
        
        # Save to session
        session['subscription_otp'] = otp
        session['subscription_email'] = email
        session['subscription_prefs'] = preferences_raw
        session['otp_timestamp'] = datetime.utcnow().timestamp()
        
        # Send Email
        if utils.send_otp_email(email, otp):
             return jsonify({"success": True, "message": "OTP sent."})
        else:
             return jsonify({"success": False, "message": "Failed to send email. Please try again."}), 500

    elif action == 'verify':
        user_otp = request.form.get('otp')
        if not user_otp:
             json_data = request.get_json(silent=True)
             if json_data:
                 user_otp = json_data.get('otp')
        
        session_otp = session.get('subscription_otp')
        session_email = session.get('subscription_email')
        session_prefs = session.get('subscription_prefs')
        timestamp = session.get('otp_timestamp', 0)
        
        if not session_otp or not user_otp:
             return jsonify({"success": False, "message": "Invalid session. Please request a new code."}), 400
             
        if datetime.utcnow().timestamp() - timestamp > 600: # 10 minutes
             return jsonify({"success": False, "message": "Code expired."}), 400
             
        if str(user_otp).strip() == str(session_otp).strip():
            # Success! Save to DB
            try:
                from app.models.user import Subscriber, UserPreferences
                from app.extensions import db

                # Check existence
                existing_sub = Subscriber.query.filter_by(email=session_email).first()
                if existing_sub:
                    return jsonify({"success": False, "message": "User already subscribed."}), 400
                
                # Create Subscriber
                new_sub = Subscriber(
                    email=session_email,
                    subscription_type='email',
                    created_at=datetime.utcnow()
                )
                db.session.add(new_sub)
                
                # Save preferences
                if session_prefs:
                    try:
                        if isinstance(session_prefs, str):
                            prefs_dict = json.loads(session_prefs)
                        else:
                            prefs_dict = session_prefs
                        
                        # Check existing prefs
                        user_pref = UserPreferences.query.filter_by(email=session_email).first()
                        if not user_pref:
                             user_pref = UserPreferences(email=session_email)
                             db.session.add(user_pref)
                        
                        user_pref.alert_thresholds = json.dumps(prefs_dict)
                        user_pref.notification_channels = json.dumps(["email"])
                        
                    except Exception as e:
                        logger.error(f"Error saving prefs: {e}")
                            
                db.session.commit()
                
                # Clear session
                session.pop('subscription_otp', None)
                session.pop('subscription_prefs', None)
                
                return jsonify({"success": True, "message": "Subscribed successfully!"})
            except Exception as e:
                db.session.rollback()
                logger.error(f"Subscription DB error: {e}")
                return jsonify({"success": False, "message": "Database error occurred."}), 500
        else:
            return jsonify({"success": False, "message": "Incorrect code."}), 400
            
    return jsonify({"success": False, "message": "Invalid action."}), 400

@subscribe_bp.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
    if request.method == "POST":
        email = request.form.get("email")
        if not email:
            flash("Please provide an email address.", "danger")
            return redirect(url_for('subscribe.unsubscribe'))
            
        try:
            with get_db() as conn:
                conn.execute("DELETE FROM subscriptions WHERE email = ?", (email,))
                conn.execute("DELETE FROM user_preferences WHERE email = ?", (email,))
                conn.commit()
            
            return render_template("unsubscribe.html", success=True)
        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
            flash("An error occurred. Please try again.", "danger")
            return redirect(url_for('subscribe.unsubscribe'))
    
    # GET request
    email_qs = request.args.get("email", "")
    return render_template("unsubscribe.html", email=email_qs)
