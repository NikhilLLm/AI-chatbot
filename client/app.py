from flask import Flask, render_template, request, jsonify
import requests
import json
import uuid

app = Flask(__name__)

# Backend server configuration
BACKEND_URL = "http://127.0.0.1:3500"
REQUEST_TIMEOUT = 5  # seconds

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_token', methods=['POST'])
def get_token():
    """Get a new chat token from the backend"""
    try:
        name = request.json.get('name', '')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        response = requests.post(f"{BACKEND_URL}/token", params={'name': name}, timeout=REQUEST_TIMEOUT)
        # Try to forward JSON if available, otherwise forward text
        if response.headers.get('content-type', '').startswith('application/json'):
            body = response.json()
        else:
            body = {'error': response.text or 'Unexpected response from backend'}

        return jsonify(body), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Backend request timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to backend server'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    """Refresh an existing chat token"""
    try:
        token = request.json.get('token', '')
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        response = requests.post(f"{BACKEND_URL}/refresh_token", params={'token': token}, timeout=REQUEST_TIMEOUT)
        if response.headers.get('content-type', '').startswith('application/json'):
            body = response.json()
        else:
            body = {'error': response.text or 'Unexpected response from backend'}

        return jsonify(body), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Backend request timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to backend server'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_backend')
def test_backend():
    """Test connection to backend server"""
    try:
        response = requests.get(f"{BACKEND_URL}/test", timeout=REQUEST_TIMEOUT)
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
        else:
            data = {'msg': response.text}

        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Backend is running', 'data': data})
        else:
            return jsonify({'status': 'error', 'message': 'Backend returned error', 'data': data}), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({'status': 'error', 'message': 'Backend request timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'status': 'error', 'message': 'Cannot connect to backend server'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
