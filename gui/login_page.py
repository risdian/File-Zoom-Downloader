import tkinter as tk
from db.database import get_config_item, upsert_config_item  # Ensure this import is correct based on your project structure
from core.zoom_auth import get_zoom_access_token

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.checkbox_state = tk.BooleanVar()

        # Create and position the login section
        client_id_label = tk.Label(self, text="Client ID:")
        client_id_label.grid(row=0, column=0, padx=5, pady=5)

        self.client_id_entry = tk.Entry(self)
        self.client_id_entry.insert(0, '')
        self.client_id_entry.grid(row=0, column=1, padx=5, pady=5)

        account_id_label = tk.Label(self, text="Account ID:")
        account_id_label.grid(row=1, column=0, padx=5, pady=5)

        self.account_id_entry = tk.Entry(self)
        self.account_id_entry.insert(0, '')
        self.account_id_entry.grid(row=1, column=1, padx=5, pady=5)

        client_secret_label = tk.Label(self, text="Client secret:")
        client_secret_label.grid(row=2, column=0, padx=5, pady=5)

        self.client_secret_entry = tk.Entry(self)
        self.client_secret_entry.insert(0, '')
        self.client_secret_entry.grid(row=2, column=1, padx=5, pady=5)

        # ... (rest of your widgets)

        # Create the login button
        login_button = tk.Button(self, text="Login", command=self.attempt_login)
        login_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # ... (checkbox and other components)
        login_checkbox = tk.Checkbutton(self, text="Remember me", variable=self.checkbox_state)
        login_checkbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5)  # Notice the row is set to 4

        self.load_default_settings()

    def attempt_login(self):
        # Example authentication logic
        auth_success = self.authenticate()  # Replace with your actual authentication logic

        if auth_success:
            # If authentication is successful and checkbox is checked, save the client_id
            if self.checkbox_state.get():
                client_id = self.client_id_entry.get()
                account_id = self.account_id_entry.get()  # Assuming you have this entry
                client_secret = self.client_secret_entry.get()  # Assuming you have this entry

                # Save the values to the database
                upsert_config_item('client_id', client_id)
                upsert_config_item('account_id', account_id)
                upsert_config_item('client_secret', client_secret)

            # Proceed to the schedule page
            self.controller.show_schedule_page()
        else:
            # Handle failed authentication
            pass

    def authenticate(self):
        # Retrieve values from the entry widgets
        client_id = self.client_id_entry.get()
        account_id = self.account_id_entry.get()
        client_secret = self.client_secret_entry.get()

        # Call the API to authenticate and get the access token
        access_token = get_zoom_access_token(client_id, account_id, client_secret)

        if access_token:
            # Authentication is successful, you can use the access token for further API calls
            # Optionally, you can store the access token securely
            return True
        else:
            # Authentication failed
            return False

    def load_default_settings(self):
        # Fetch and insert default client ID
        default_client_id = get_config_item('client_id')
        default_account_id = get_config_item('account_id')
        default_client_secret = get_config_item('client_secret')

        if default_client_id:
            self.client_id_entry.delete(0, tk.END)  # Clear existing content
            self.client_id_entry.insert(0, default_client_id)
        if default_account_id:
            self.account_id_entry.delete(0, tk.END)  # Clear existing content
            self.account_id_entry.insert(0, default_account_id)
        if default_client_secret:
            self.client_secret_entry.delete(0, tk.END)  # Clear existing content
            self.client_secret_entry.insert(0, default_client_secret)