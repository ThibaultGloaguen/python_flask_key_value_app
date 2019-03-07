from flask import jsonify, request, abort, make_response, Blueprint
from appplication.service.key_store_service import KeyStoreService
from appplication import error_counter

store_service = KeyStoreService()

views = Blueprint('views', __name__, url_prefix='/')


@views.route('/keys/<id>', methods=['GET'])
def get(id):
    if not store_service.exists(id):
        abort(404)
    value_entity = store_service.get_entity(id)
    if value_entity.is_expired:
        abort(410)
    return jsonify({'response': value_entity.value})


@views.route('/keys', methods=['GET'])
def get_all():
    filter = request.args.get('filter')
    all_available_values = store_service.get_values(filter)
    return jsonify({'response': all_available_values})


@views.route('/keys', methods=['PUT'])
def put():
    expire_in = request.args.get('expire_in')
    json_payload = request.json
    if not json_payload:
        abort(400)
    keys_not_persisted = store_service.set_entity(json_payload, expire_in)
    message = 'all key value pair are persisted'
    if len(keys_not_persisted) > 0:
        message = 'keys %s were not persisted in database' % ', '.join(keys_not_persisted)
    return jsonify({'response': message})


@views.route('/keys/<id>', methods=['DELETE'])
def delete(id):
    if not store_service.exists(id):
        abort(404)
    is_deleted = store_service.delete(id)
    message = '%s has been deleted' % id
    if not is_deleted:
        message = 'impossible to delete %s' % id
    return jsonify({'response': message})


@views.route('/keys', methods=['DELETE'])
def delete_all():
    is_all_key_deleted = store_service.delete_all()
    message = 'all keys have been deleted'
    if not is_all_key_deleted:
        message = 'impossible to delete all keys'
    return jsonify({'response': message})


@views.errorhandler(404)
def not_found(error):
    error_counter.labels(error_code='404', description='Entity not found').inc()
    return make_response(jsonify({'error': 'Not found'}), 404)


@views.errorhandler(400)
def bad_request(error):
    error_counter.labels(error_code='400', description='Bad request').inc()
    return make_response(jsonify({'error': 'Bad request'}), 400)


@views.errorhandler(410)
def expired(error):
    error_counter.labels(error_code='410', description='Entity expired').inc()
    return make_response(jsonify({'error': 'Expired'}), 410)


@views.errorhandler(500)
def server_error(error):
    print error.message
    error_counter.labels(error_code='500', description='Internal error').inc()
    return make_response(jsonify({'error': 'Internal error :('}), 500)