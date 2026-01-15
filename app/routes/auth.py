from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from ..database import get_db
from .. import utils
import requests
import json
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/profile")
def profile():
    """User Profile Page."""
    if 'user_email' not in session:
        return render_template("profile.html", active_page="profile", date_time_info=utils.get_local_time_string(), user=None)
    
    email = session['user_email']
    user_data = {}
    
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get Subscription Info
        c.execute("SELECT * FROM subscriptions WHERE email = ?", (email,))
        sub = c.fetchone()
        if sub:
            user_data['subscription'] = dict(sub)
            
        # Get Preferences
        c.execute("SELECT * FROM user_preferences WHERE email = ?", (email,))
        prefs = c.fetchone()
        if prefs:
            user_data['preferences'] = dict(prefs)
            try:
                 if user_data['preferences'].get('activities'):
                     user_data['preferences']['activities'] = json.loads(user_data['preferences']['activities'])
            except:
                 user_data['preferences']['activities'] = []
                 
            try:
                 if user_data['preferences'].get('dashboard_config'):
                     user_data['preferences']['dashboard_config'] = json.loads(user_data['preferences']['dashboard_config'])
            except:
                 user_data['preferences']['dashboard_config'] = {}
        else:
             user_data['preferences'] = {"temperature_unit": "C", "activities": [], "dashboard_config": {}}

        # Get Favorites
        c.execute("SELECT * FROM favorite_locations WHERE email = ? ORDER BY created_at DESC", (email,))
        favs = [dict(row) for row in c.fetchall()]
        
    # We should probably pass favs to template too, but keeping original logic
    # Original code didn't assign favs to user_data['favorites'] explicitly in the view code showed above, 
    # but let's check if the template uses it. The view code ended with just `user=user_data`.
    # Let's add it just in case.
    user_data['favorites'] = favs
    
    return render_template("profile.html", active_page="profile", date_time_info=utils.get_local_time_string(), user=user_data)

@auth_bp.route("/api/user/logout", methods=["POST"])
def logout():
    session.pop('user_email', None)
    return jsonify({"success": True})

@auth_bp.route("/api/user/profile", methods=["GET", "POST"])
def api_user_profile():
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = session['user_email']
    
    if request.method == "GET":
        pass

    if request.method == "POST":
        data = request.json
        temp_unit = data.get("temperature_unit")
        activities = data.get("activities")
        dashboard_config = data.get("dashboard_config")
        language = data.get("language", "en")
        timezone_pref = data.get("timezone")
        currency = data.get("currency", "USD")
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM user_preferences WHERE email = ?", (email,))
                exists = cursor.fetchone()
                
                if exists:
                    conn.execute("""
                        UPDATE user_preferences 
                        SET temperature_unit = ?, activities = ?, dashboard_config = ?, 
                            language = ?, timezone = ?, currency = ?
                        WHERE email = ?
                    """, (temp_unit, json.dumps(activities), json.dumps(dashboard_config), 
                          language, timezone_pref, currency, email))
                else:
                    conn.execute("""
                        INSERT INTO user_preferences (email, temperature_unit, activities, dashboard_config, language, timezone, currency)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (email, temp_unit, json.dumps(activities), json.dumps(dashboard_config), 
                          language, timezone_pref, currency))
                
                conn.commit()
            return jsonify({"success": True})
        except Exception as e:
            current_app.logger.error(f"Profile update error: {e}")
            return jsonify({"error": str(e)}), 500

@auth_bp.route("/api/user/favorites", methods=["GET", "POST", "DELETE"])
def api_user_favorites():
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = session['user_email']
    
    if request.method == "GET":
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM favorite_locations WHERE email = ? ORDER BY created_at DESC", (email,))
            rows = [dict(r) for r in c.fetchall()]
        return jsonify(rows)

    if request.method == "POST":
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        city = data.get('city')
        country = data.get('country')
        
        if not lat or not lon:
            return jsonify({"error": "Missing coordinates"}), 400
            
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM favorite_locations WHERE email = ? AND lat = ? AND lon = ?", (email, lat, lon))
            if c.fetchone():
                return jsonify({"success": True, "message": "Already a favorite"})
                
            conn.execute(
                "INSERT INTO favorite_locations (email, lat, lon, city, country, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (email, lat, lon, city, country, datetime.utcnow().isoformat())
            )
            conn.commit()
        return jsonify({"success": True})

    if request.method == "DELETE":
        fav_id = request.args.get('id')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        with get_db() as conn:
            if fav_id:
                conn.execute("DELETE FROM favorite_locations WHERE id = ? AND email = ?", (fav_id, email))
            elif lat and lon:
                conn.execute("DELETE FROM favorite_locations WHERE lat = ? AND lon = ? AND email = ?", (lat, lon, email))
            conn.commit()
        return jsonify({"success": True})

@auth_bp.route("/api/update-session-location", methods=["POST"])
def update_session_location():
    """Update server-side session with client-granted location info."""
    data = request.get_json(silent=True) or {}
    city = data.get("city")
    region = data.get("region")
    utc_offset = data.get("utc_offset")
    
    if city and utc_offset:
        ip = utils.get_client_ip()
        session["location_data"] = {
            "ip": ip,
            "city": city,
            "region": region,
            "utc_offset": utc_offset
        }
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Missing data"}), 400
