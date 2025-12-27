import sys
import os

# Set environment variable to indicate we're on Vercel
os.environ['VERCEL'] = '1'

try:
    # Import the Flask app
    from app import app
    
    # Vercel expects the WSGI app to be available as a module-level variable
    # No need for a custom handler function
    
except Exception as e:
    # Log the error for debugging
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    
    # Create a minimal error app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return jsonify({
            "error": "Failed to initialize application",
            "message": str(e),
            "type": type(e).__name__
        }), 500

