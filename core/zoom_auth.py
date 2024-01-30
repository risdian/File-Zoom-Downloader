import base64
import json
import requests
from db.database import get_config_item, upsert_config_item, upsert_user, mark_users_as_deleted  # Ensure this import is correct based on your project structure

def get_zoom_access_token(client_id, account_id, client_secret):

    url = "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=" + account_id

    client_cred = client_id + ":" + client_secret
    client_cred_base64_string = base64.b64encode(client_cred.encode('utf-8')).decode('utf-8')

    headers = {
        'Authorization': 'Basic ' + client_cred_base64_string,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        jdata = response.json()

        access_token = jdata.get("access_token")
        if access_token:
            upsert_config_item('access_token', access_token)
            return access_token
        else:
            # Handle the case where no token is provided
            return None
    except requests.RequestException as e:
        # Handle exceptions
        print(f"Error during authentication: {e}")
        return None
    

def is_access_token_valid():
    access_token = get_config_item('access_token')
    print(access_token)

    if not access_token:
        return False

    # Example API endpoint to validate token
    url = 'https://api.zoom.us/v2/users/me'

    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except requests.RequestException:
        return False

def populate_all_users():
    access_token = get_config_item('access_token')

    if not access_token:
        return False

    url = 'https://api.zoom.us/v2/users'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Parse the JSON response
            response_data = response.json()
            # Use the 'get' method on the parsed JSON (which is a dictionary)
            users = response_data.get("users", [])
            process_and_save_users(users)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error fetching users from Zoom: {e}")
        return False
    

def process_and_save_users(users):
    mark_users_as_deleted()

    # users = api_response.get("users", [])
    for user_data in users:
        upsert_user({
            'id': user_data['id'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'display_name': user_data['display_name'],
            'email': user_data['email'],
            'type': user_data['type'],
            'timezone': user_data['timezone'],
            'verified': user_data['verified'],
            'created_at': user_data['created_at'],
            'last_login_time': user_data['last_login_time'],
            'status': user_data['status']
        })


def fetch_user_recordings(user_email, start_date, end_date):
    url = f"https://api.zoom.us/v2/users/{user_email}/recordings?from={start_date}&to={end_date}"
    headers = {
        'Authorization': 'Bearer ' + get_config_item('access_token'),
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('meetings', [])        
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching recordings for {user_email}: {e}")
        return None
    

