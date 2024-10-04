from flask_jwt_extended import jwt_required
from utilities import Context

app = Context().app()

# Route to get sensor info
@app.route("/get_sensor_info", methods=["GET"])
@jwt_required(optional = False)
def get_sensor_info():



    return flask.jsonify(logged_in_as = current_user.username), 200



