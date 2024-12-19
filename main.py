import os
from app import app

if __name__ == "__main__":
    try:
        # Get port from environment variable or default to 5000
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    except OSError as e:
        if "Address already in use" in str(e):
            # Try alternative port if 5000 is in use
            alt_port = 5001
            print(f"Port {port} is in use, trying port {alt_port}")
            app.run(host="0.0.0.0", port=alt_port)
        else:
            raise e
