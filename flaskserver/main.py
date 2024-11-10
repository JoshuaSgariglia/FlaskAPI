from core import Context
from authentication import bp as authentication_blueprint
from api import bp as api_blueprint

# Get the app reference from Context
app = Context().app()

# Register Blueprints
app.register_blueprint(authentication_blueprint)
app.register_blueprint(api_blueprint)

# Entry point for the application
if __name__ == "__main__":
    # Set the port for the application, this is only for development
    # turn debug on in development
    app.run(port=5004, debug=True)
