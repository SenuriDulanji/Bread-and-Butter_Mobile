from app import app
from config import Config

if __name__ == '__main__':
    config = Config()
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )