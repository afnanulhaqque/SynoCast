import sys
import os
import traceback as tb

# Set environment variable to indicate we're on Vercel
os.environ['VERCEL'] = '1'

app = None
import_error = None

try:
    # Import the Flask app
    from app import app
    print("✓ App imported successfully!", file=sys.stderr)
    
except Exception as e:
    # Capture the full error
    import_error = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": tb.format_exc()
    }
    
    # Log to stderr for Vercel logs
    print(f"✗ ERROR: Failed to import app!", file=sys.stderr)
    print(f"Error type: {type(e).__name__}", file=sys.stderr)
    print(f"Error message: {str(e)}", file=sys.stderr)
    print("Full traceback:", file=sys.stderr)
    print(tb.format_exc(), file=sys.stderr)
    
    # Create a minimal error app that shows the actual error
    from flask import Flask, jsonify, render_template_string
    app = Flask(__name__)
    
    ERROR_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SynoCast - Deployment Error</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                margin: 0;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: rgba(0,0,0,0.3);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            h1 { color: #ff6b6b; margin-top: 0; }
            h2 { color: #ffd93d; margin-top: 30px; }
            .error-box {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #ff6b6b;
            }
            pre {
                background: rgba(0,0,0,0.5);
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .success { color: #6bcf7f; }
            .warning { color: #ffd93d; }
            .error { color: #ff6b6b; }
            ul { line-height: 1.8; }
            code {
                background: rgba(0,0,0,0.3);
                padding: 2px 6px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚠️ SynoCast Deployment Error</h1>
            <p>The application failed to start. Here's the detailed error information:</p>
            
            <div class="error-box">
                <h2>Error Details</h2>
                <p><strong>Type:</strong> <code>{{ error.type }}</code></p>
                <p><strong>Message:</strong> {{ error.error }}</p>
            </div>
            
            <div class="error-box">
                <h2>Full Traceback</h2>
                <pre>{{ error.traceback }}</pre>
            </div>
            
            <h2>Common Solutions</h2>
            <ul>
                <li><strong>Missing Environment Variables:</strong> Go to Vercel Dashboard → Settings → Environment Variables and add all required variables</li>
                <li><strong>Missing Dependencies:</strong> Check if the error mentions a missing module, then add it to requirements.txt</li>
                <li><strong>File Not Found:</strong> Verify all files are committed to Git and not in .gitignore</li>
                <li><strong>After fixing:</strong> Redeploy from Vercel Dashboard</li>
            </ul>
            
            <h2>Required Environment Variables</h2>
            <ul>
                <li>FLASK_SECRET_KEY</li>
                <li>OPENWEATHER_API_KEY</li>
                <li>RESEND_API_KEY</li>
                <li>GEMINI_API_KEY</li>
                <li>NEWS_API_KEY</li>
                <li>VAPID_PRIVATE_KEY</li>
                <li>VAPID_PUBLIC_KEY</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    @app.route('/')
    @app.route('/<path:path>')
    def error_page(path=None):
        return render_template_string(ERROR_TEMPLATE, error=import_error), 500
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "error",
            "error": import_error
        }), 500

