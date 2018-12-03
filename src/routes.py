import json
from db import db, Location, Machine
from flask import Flask, request

db_filename = 'network.db'
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % db_filename
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def is_valid_location(location_id):
    location = Location.query.filter_by(id=location_id).first()
    return not location is None


# returns all locations
@app.route('/api/locations/', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    data = [location.serialize() for location in locations]
    return json.dumps({'success': True, 'data': data }), 200


# returns the machines at location <location_id>
@app.route('/api/locations/<int:location_id>/machines/', methods=['GET'])
def get_machines_in_location(location_id):
    location = Location.query.filter_by(id=location_id).first()
    if not location is None:
        data = [ machine.serialize() for machine in location.machines ]
        return json.dumps({'success': True, 'data': data}), 200
    return json.dumps({'success': False, 'error': 'Location with ID ' + str(location_id) + ' not found.'}), 404


# returns True if machine <machine_id> is a washer, False if it's a dryer
@app.route('/api/machines/<int:machine_id>/type/', methods=['GET'])
def get_machine_type(machine_id):
    machine = Machine.query.filter_by(id=machine_id).first()
    if not machine is None:
        return json.dumps({'success': True, 'data': {'washer': machine.washer}})
    return json.dumps({'success': False, 'error': 'Machine with ID ' + str(machine_id) + ' not found.'}), 404


# returns the time remaining on machine <machine_id> in seconds
@app.route('/api/machines/<int:machine_id>/time/', methods=['GET'])
def get_machine_time_remaining(machine_id):
    machine = Machine.query.filter_by(id=machine_id).first()
    if not machine is None:
        return json.dumps({'success': True, 'data': {'time_remaining': machine.get_time_remaining()}})
    return json.dumps({'success': False, 'error': 'Machine with ID ' + str(machine_id) + ' not found.'}), 404


# returns the status of machine <machine_id>; 0 for available, 1 for in use, 2 for broken
@app.route('/api/machines/<int:machine_id>/status/')
def get_machine_status(machine_id):
    machine = Machine.query.filter_by(id=machine_id).first()
    if not machine is None:
        return json.dumps({'success': True, 'data': {'status': machine.get_status()}})
    return json.dumps({'success': False, 'error': 'Machine with ID ' + str(machine_id) + ' not found.'}), 404


# starts a timer for machine <machine_id> with duration <duration> passed in the request body
@app.route('/api/machines/<int:machine_id>/start/', methods=['POST'])
def start_machine_timer(machine_id):
    machine = Machine.query.filter_by(id=machine_id).first()
    if not machine is None:
        request_body = json.loads(request.data)
        duration = request_body.get('duration', None)
        if duration is None or type(duration) != int:
            return json.dumps({'success': False, 'data': 'Could not start machine timer without specification of the session duration.'}), 400
        else:
            machine.initiate_session(int(duration))
            db.session.commit()
            return json.dumps({'success': True, 'data': machine.serialize()}), 200
    return json.dumps({'success': False, 'error': 'Machine with ID ' + str(machine_id) + ' not found.'}), 404


# returns the new location that was created; empty request body
@app.route('/api/locations/create/', methods=['POST'])
def create_location():
    request_body = json.loads(request.data)

    location = Location(name = request_body.get('name', 'unnamed-location'))

    db.session.add(location)
    db.session.commit()

    return json.dumps({'success': True, 'data': location.serialize()}), 201


# returns the new machine that was created; request body must include location <location_id>,
# <washer> with True signifiying a washer and False signifying a dryer, <status>
# with 0 signifying available, 1 in use, and 2 out of order,
@app.route('/api/machines/create/', methods=['POST'])
def create_machine():
    request_body = json.loads(request.data)
    location_id = request_body.get('location_id', -1)
    if location_id == -1:
        return json.dumps({'success': False, 'data': 'Could not create machine without specification of location ID.'}), 400
    if not is_valid_location(location_id):
        return json.dumps({'success': False, 'data': 'Location with ID ' + str(location_id) + ' not found.'}), 404

    machine = Machine(
        washer = request_body.get('washer', True),
        status = request_body.get('status', 0),
        location_id = location_id
    )
    db.session.add(machine)
    db.session.commit()

    return json.dumps({'success': True, 'data': machine.serialize()}), 201


# returns the location with id <location_id> that was deleted
@app.route('/api/locations/<int:location_id>/', methods=['DELETE'])
def delete_location(location_id):
    location = Location.query.filter_by(id=location_id).first()
    if location is not None:
        db.session.delete(location)
        db.session.commit()
        return json.dumps({'success': True, 'data': location.serialize()}), 200
    return json.dumps({'success': False, 'error': 'Location with ID ' + str(location_id) + ' not found.'}), 404


# returns the machine with id <machine_id> that was deleted
@app.route('/api/machines/<int:machine_id>/', methods=['DELETE'])
def delete_machine(machine_id):
    machine = Machine.query.filter_by(id=machine_id).first()
    if machine is not None:
        db.session.delete(machine)
        db.session.commit()
        return json.dumps({'success': True, 'data': machine.serialize()}), 200
    return json.dumps({'success': False, 'error': 'Machine with ID ' + str(machine_id) + ' not found.'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
