from flask import Flask
from config import Config
from datetime import datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Add datetimeformat filter
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                return value
        if isinstance(value, int):
            return datetime.fromtimestamp(value).strftime(format)
        return value

    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app