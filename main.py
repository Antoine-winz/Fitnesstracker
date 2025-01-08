import os
import logging
from app import app

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get the Replit assigned port
    server_port = int(os.environ.get('PORT', '3000'))

    try:
        logger.info(f"Starting server on port {server_port}")
        logger.info(f"Server domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'Not set')}")

        app.run(
            host='0.0.0.0',
            port=server_port,
            debug=True
        )
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise