import flask
from flask_jwt_extended import current_user, jwt_required
import requests

# Define Blueprint
bp = flask.Blueprint('database', __name__)

# Route to get sensor info
@bp.route("/get_sensor_info", methods=["GET"])
@jwt_required(optional = False)
def get_sensor_info():
    try:
        print(flask.jsonify(requests.get(url="http://192.168.104.78:5000/api/data?sensor_id=http:%2F%2Fhomey\%2Fexample_graph%2Fsensor_mix_kitchen")))
    except Exception as e:
        print(e)

    return {}, 200


