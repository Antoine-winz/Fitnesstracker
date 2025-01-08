import os
from app import app

if __name__ == '__main__':
    # Get the Replit assigned port
    server_port = int(os.environ.get('PORT', '3000'))

    print(f"\nStarting server on port {server_port}")
    print(f"Server domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'Not set')}")

    app.run(
        host='0.0.0.0',
        port=server_port,
        debug=True
    )