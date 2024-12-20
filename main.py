
import os
from app import app

if __name__ == '__main__':
    # Get the Replit assigned port
    server_port = int(os.environ.get('PORT', '3000'))
    
    print(f"Starting server on port {server_port}")
    print(f"Server domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'Not set')}")
    
    # Run the Flask application with the correct host and port
    app.run(
        host='0.0.0.0',  # Required to accept external connections
        port=server_port,
        debug=True,  # Enable debug mode for development
    )
