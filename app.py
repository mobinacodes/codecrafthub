"""
CodeCraftHub - Learning Platform REST API
A simple Flask application to track and manage learning courses
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = 'courses.json'
VALID_STATUSES = ['Not Started', 'In Progress', 'Completed']


def load_courses():
    """Load all courses from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError):
        return []


def save_courses(courses):
    """Save all courses to the JSON file."""
    try:
        with open(DATA_FILE, 'w') as file:
            json.dump(courses, file, indent=2)
        return True
    except IOError as e:
        print(f"Error writing to {DATA_FILE}: {e}")
        return False


def get_next_course_id():
    """Generate the next available course ID."""
    courses = load_courses()
    if not courses:
        return 1
    return max(course['id'] for course in courses) + 1


def validate_course_data(data):
    """Validate course data before creating/updating."""
    if not isinstance(data, dict):
        return False, "Request body must be JSON"

    required_fields = ['name', 'description', 'target_date', 'status']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: '{field}'"
        if not data[field] or (isinstance(data[field], str) and data[field].strip() == ''):
            return False, f"Field '{field}' cannot be empty"

    if data['status'] not in VALID_STATUSES:
        return False, f"Invalid status '{data['status']}'. Must be one of: {', '.join(VALID_STATUSES)}"

    try:
        datetime.strptime(data['target_date'], '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-25)"

    return True, "Valid"


def find_course(course_id):
    """Find a course by ID. Returns the course dict or None."""
    courses = load_courses()
    return next((c for c in courses if c['id'] == course_id), None)


# ==================== Routes ====================

@app.route('/api/courses', methods=['GET'])
def get_all_courses():
    courses = load_courses()
    return jsonify({
        'success': True,
        'count': len(courses),
        'data': courses
    }), 200


@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = find_course(course_id)
    if not course:
        return jsonify({
            'success': False,
            'message': f'Course with ID {course_id} not found'
        }), 404
    return jsonify({'success': True, 'data': course}), 200


@app.route('/api/courses', methods=['POST'])
def create_course():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'success': False, 'message': 'Invalid or missing JSON body'}), 400

    is_valid, message = validate_course_data(data)
    if not is_valid:
        return jsonify({'success': False, 'message': message}), 400

    courses = load_courses()
    new_course = {
        'id': get_next_course_id(),
        'name': data['name'],
        'description': data['description'],
        'target_date': data['target_date'],
        'status': data['status'],
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    courses.append(new_course)

    if not save_courses(courses):
        return jsonify({'success': False, 'message': 'Failed to save course'}), 500

    return jsonify({
        'success': True,
        'message': 'Course created successfully',
        'data': new_course
    }), 201


@app.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)

    if not course:
        return jsonify({
            'success': False,
            'message': f'Course with ID {course_id} not found'
        }), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'success': False, 'message': 'Invalid or missing JSON body'}), 400

    # Allow partial updates: only validate fields that were actually sent
    if 'status' in data and data['status'] not in VALID_STATUSES:
        return jsonify({
            'success': False,
            'message': f"Invalid status '{data['status']}'. Must be one of: {', '.join(VALID_STATUSES)}"
        }), 400

    if 'target_date' in data:
        try:
            datetime.strptime(data['target_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

    for field in ['name', 'description', 'target_date', 'status']:
        if field in data:
            course[field] = data[field]

    if not save_courses(courses):
        return jsonify({'success': False, 'message': 'Failed to save course'}), 500

    return jsonify({
        'success': True,
        'message': 'Course updated successfully',
        'data': course
    }), 200


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)

    if not course:
        return jsonify({
            'success': False,
            'message': f'Course with ID {course_id} not found'
        }), 404

    courses = [c for c in courses if c['id'] != course_id]

    if not save_courses(courses):
        return jsonify({'success': False, 'message': 'Failed to delete course'}), 500

    return jsonify({
        'success': True,
        'message': f'Course with ID {course_id} deleted successfully'
    }), 200


@app.route('/api/courses/status/<status>', methods=['GET'])
def get_courses_by_status(status):
    courses = load_courses()
    filtered = [c for c in courses if c['status'] == status]
    return jsonify({
        'success': True,
        'count': len(filtered),
        'data': filtered
    }), 200


if __name__ == '__main__':
    print("- CodeCraftHub API is starting...")
    print(f"- Data will be stored in: {os.path.abspath(DATA_FILE)}")
    print("- API will be available at: http://localhost:5000")
    app.run(debug=True, port=5001)

