import os
import logging
from app import app

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get the Replit assigned port
    server_port = int(os.environ.get('PORT', '3000'))
    server_host = '0.0.0.0'  # Listen on all available interfaces

    try:
        logger.info(f"Starting server on {server_host}:{server_port}")
        logger.info(f"Server domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'Not set')}")
        logger.info(f"Full server URL: https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}:{server_port}")

        app.run(
            host=server_host,
            port=server_port,
            debug=True
        )
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise