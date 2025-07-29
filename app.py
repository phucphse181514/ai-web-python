from app import create_app
import logging

app = create_app()

if __name__ == '__main__':
    # Enable debug logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)
