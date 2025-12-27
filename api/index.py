import sys
import os

# Set environment variable to indicate we're on Vercel
os.environ['VERCEL'] = '1'

try:
    from app import app
    
    # Vercel serverless function handler
    def handler(event, context):
        return app(event, context)
        
except Exception as e:
    # Log the error for debugging
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    raise
