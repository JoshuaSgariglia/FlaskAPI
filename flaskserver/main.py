from utilities import Context
from models import User

# Get the references from Context
app = Context().app()
db = Context().db()

# Base route
@app.route('/')
def testdb():
    user_dict: dict = db.session.query(User).all()[0].__dict__
    print(user_dict)
    user_dict.pop("_sa_instance_state")
    return user_dict

# Entry point for the application
if __name__ == "__main__":
    # Set the port for the application, this is only for development
    # turn debug on in development
    app.run(port=5004, debug=True)
