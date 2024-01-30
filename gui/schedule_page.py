import tkinter as tk
from tkinter import ttk
import sys
from tkinter.filedialog import askdirectory
from tkinter import messagebox
from db.database import delete_all_users, record_download, get_download_history,  update_download_record, record_or_update_download_status, check_download_status, upsert_config_item,delete_config_item, get_all_users
from core.zoom_auth import populate_all_users, fetch_user_recordings
from datetime import datetime, timedelta
import threading
import requests
import os
import queue
import schedule
import time
from db.database import get_config_item # Ensure this import is correct based on your project structure
from core.downloader import download_file
from dateutil.parser import parse

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class SchedulePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent  # Store the parent widget
        self.download_link_map = {}  # Dictionary to map Treeview items to download links
        self.selected_folder_path = None  # Initialize the selected folder path variable

        # Create a queue for download tasks
        self.download_queue = queue.Queue()
        self.cancel_flags = {}

        # Start the worker thread
        self.start_download_worker()

        # Configure grid row and column weights
        self.grid_rowconfigure(0, weight=1)
        for col in range(3):  # Adjust the range as needed
            self.grid_columnconfigure(col, weight=1)

        self.checkbox_state = tk.BooleanVar()
        self.create_context_menu()


        label = tk.Label(self, text="This is the Schedule Page")
        label.grid(row=0, column=0, columnspan=1, padx=10, pady=10)

        logout_button = tk.Button(self, text="Logout", command=self.logout)
        logout_button.grid(row=0, column=1, columnspan=1, pady=10)

        user_select_label = tk.Label(self, text="Select User:")
        user_select_label.grid(row=1, column=0, padx=10, pady=5)

        self.user_combobox = ttk.Combobox(self, state="readonly")
        self.user_combobox.grid(row=1, column=1, padx=10, pady=5)
        self.populate_user_combobox()

        start_date_label = tk.Label(self, text="Start Date:")
        start_date_label.grid(row=2, column=0, padx=5, pady=5)

        self.start_date_entry = tk.Entry(self)
        self.start_date_entry.insert(0, '2024-01-28')
        self.start_date_entry.grid(row=2, column=1, padx=5, pady=5)

        end_date_label = tk.Label(self, text="End Date:")
        end_date_label.grid(row=3, column=0, padx=5, pady=5)

        self.end_date_entry = tk.Entry(self)
        self.end_date_entry.insert(0, '2024-01-29')
        self.end_date_entry.grid(row=3, column=1, padx=5, pady=5)

        download_start_time_label = tk.Label(self, text="Start Time:")
        download_start_time_label.grid(row=4, column=0, padx=5, pady=5)

        self.start_time_entry = tk.Entry(self)
        self.start_time_entry.insert(0, '01:30')
        self.start_time_entry['state'] = 'disabled'  # Set the state to 'disabled'
        self.start_time_entry.grid(row=4, column=1, padx=5, pady=5)

        download_end_time_label = tk.Label(self, text="End Time Time:")
        download_end_time_label.grid(row=5, column=0, padx=5, pady=5)

        self.end_time_entry = tk.Entry(self)
        self.end_time_entry.insert(0, '13:30')
        self.end_time_entry['state'] = 'disabled'  # Set the state to 'disabled'
        self.end_time_entry.grid(row=5, column=1, padx=5, pady=5)

        download_time_label = tk.Label(self, text="Download Time:")
        download_time_label.grid(row=6, column=0, padx=5, pady=5)

        self.download_time_entry = tk.Entry(self)
        self.download_time_entry.insert(0, '03:30')
        self.download_time_entry['state'] = 'disabled'  # Set the state to 'disabled'
        self.download_time_entry.grid(row=6, column=1, padx=5, pady=5)

        schedule_download_label = tk.Label(self, text="Schedule date?:")
        schedule_download_label.grid(row=7, column=0, padx=5, pady=5)

        schedule_checkbox = tk.Checkbutton(self, text="Schedule Download", variable=self.checkbox_state, command=self.toggle_date_time_entries)
        schedule_checkbox.grid(row=7, column=1, padx=5, pady=5)  # Notice the row is set to 4

        select_folder_button = tk.Button(self, text="Select Folder", command=self.select_folder)
        select_folder_button.grid(row=8, column=0, padx=5, pady=5)

        self.selected_folder_label = tk.Label(self, text="Selected Folder: None")
        self.selected_folder_label.grid(row=8, column=1, padx=5, pady=5)

        find_button = tk.Button(self, text="Download", command=self.start_download_schedule)
        find_button.grid(row=9, column=0, padx=5, pady=5)

        refresh_button = tk.Button(self, text="Refresh", command=self.get_all_users_from_zoom)
        refresh_button.grid(row=9, column=1, padx=5, pady=5)

        search_button = tk.Button(self, text="Search", command=self.search_meetings)
        search_button.grid(row=10, column=0, padx=5, pady=5)

        view_db = tk.Button(self, text="view Db", command=self.view_download)
        view_db.grid(row=10, column=1, padx=5, pady=5)


        # # Add the "Download List" label
        download_list_label = tk.Label(self, text="Download List")
        download_list_label.grid(row=11, column=0, padx=5, pady=5)

        # Create a frame for the download list
        download_list_frame = tk.Frame(self, width=30)
        download_list_frame.grid(row=12, column=0, columnspan=3, padx=10, pady=10)

        # Create a Text widget inside the download_list_frame for output
        self.text_widget = tk.Text(download_list_frame, height=10, width=50)
        self.text_widget.grid(row=13, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.text_widget.pack(expand=True, fill='both')

        # Redirect standard output to text_widget
        self.redirect_output(self.text_widget)
        print('Welcome zoom download manager how are you today?')
        print('Lets start with our download')

        # Add a button to delete all users
        delete_users_button = tk.Button(self, text="Delete All Users", command=self.confirm_delete_all)
        delete_users_button.grid(row=14, column=0, padx=10, pady=10)  # Adjust position as needed

        # test
        # Create the Treeview widget for the recorded download table
        self.user_tree = ttk.Treeview(self, selectmode='extended', columns=("Topic", "ID",  "Type", "Start Date", "End Date", "Download"))
        # Position the Treeview on the right side
        self.user_tree.grid(row=15, column=0, columnspan=2, rowspan=8, padx=10, pady=10)  # Adjust rowspan as needed
        self.user_tree.column("#0", width=0, stretch=tk.NO)

        # Define the column headings
        self.user_tree.heading("Topic", text="Topic")
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("Type", text="Type")
        self.user_tree.heading("Start Date", text="Start Date")
        self.user_tree.heading("End Date", text="End Date")
        self.user_tree.heading("Download", text="Download")

        self.user_tree.bind("<Button-2>", self.on_right_click)  # For Windows and Linux

        # self.load_user_data()

        self.load_default_settings()


    def toggle_date_time_entries(self):
        if self.checkbox_state.get():
            # Checkbox is checked, disable the date and time entries
            self.start_date_entry['state'] = 'disabled'
            self.end_date_entry['state'] = 'disabled'
            self.download_time_entry['state'] = 'normal'  # Enable if checked
            self.end_time_entry['state'] = 'normal'
            self.start_time_entry['state'] = 'normal'
        else:
            # Checkbox is not checked, enable the date entries and disable time entry
            self.start_date_entry['state'] = 'normal'
            self.end_date_entry['state'] = 'normal'
            self.download_time_entry['state'] = 'disabled'  # Disable if unchecked
            self.end_time_entry['state'] = 'disabled'
            self.start_time_entry['state'] = 'disabled'

    def logout(self):
        # Delete the access token from the database
        delete_config_item('access_token')

        # Redirect to the login page
        self.controller.show_login_page()

    # Function to redirect the standard output to the Text widget
    def redirect_output(self, text_widget):
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, message):
                self.text_widget.insert(tk.END, message)
                self.text_widget.see(tk.END)

            def flush(self):
                # Necessary for file-like object
                pass

        sys.stdout = StdoutRedirector(text_widget)


    def select_folder(self):
        folderpath = askdirectory()
        if folderpath:  # Check if a directory was selected
            self.selected_folder_path = folderpath  # Store the selected folder path
            self.selected_folder_label.config(text="Selected Folder: {}".format(folderpath))
            try:
                upsert_config_item('download_folder_path', folderpath)  # Update the database with the selected path
            except Exception as e:
                # Handle any exceptions that occur during database update
                print(f"Error updating database: {e}")
        else:
            self.selected_folder_label.config(text="Selected Folder: None")
    
    def get_all_users_from_zoom(self):
        populate_all_users()
        # self.load_user_data()
        pass

    def confirm_delete_all(self):
        # Ask for confirmation before deletion
        response = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all users?")
        if response:
            delete_all_users()
            # self.load_user_data()  # Refresh your user display if necessary

    def populate_user_combobox(self):
        users = get_all_users()        
        display_name = [user.display_name for user in users]
        self.user_combobox['values'] = display_name

    def search_meetings(self):
        selected_user_email = self.user_combobox.get()  # Get the selected user's email
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        
        if selected_user_email:
            # Fetch meetings for the selected user
            meetings = fetch_user_recordings(selected_user_email, start_date, end_date)
            self.populate_meetings_in_treeview(meetings)
        else:
            print("No user selected")

    def populate_meetings_in_treeview(self, meetings):
        # Clear existing data in Treeview
        self.download_link_map.clear()  # Clear the dictionary when repopulating the Treeview
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        for meeting in meetings:
            meeting_topic = meeting['topic']
            meeting_host_id = meeting['host_id']
            # Iterate over recording files
            for recording in meeting.get('recording_files', []):
                if (recording['status'] == 'completed'):
                    downloaded = check_download_status(recording['id'])
                    download_status = 'Downloaded' if downloaded else 'Not Downloaded'

                    start_date, start_time = self.format_datetime(recording['recording_start'])
                    end_date, end_time = self.format_datetime(recording['recording_end'])
                    item_id = self.user_tree.insert('', 'end', values=(meeting_topic, recording['id'], recording['recording_type'], start_date + ' - ' + start_time, end_date + ' - ' + end_time, download_status))
                    self.download_link_map[item_id] = {
                        "id": recording["id"],
                        "host_id": meeting_host_id,
                        "meeting_topic": meeting_topic,
                        "meeting_id": recording["meeting_id"],
                        "recording_start": recording["recording_start"],
                        "recording_end": recording["recording_end"],
                        "file_type": recording["file_type"],
                        "file_extension": recording["file_extension"],
                        "file_size": recording["file_size"],
                        "download_url": recording["download_url"],
                        "status": recording["status"],
                        "recording_type": recording["recording_type"]
                    }

    def format_datetime(self, dt_str):
        # Convert the ISO format string to a datetime object
        dt = datetime.fromisoformat(dt_str)
        # Format the date and time separately
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
    

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.parent, tearoff=0)  # Use self.parent instead of root
        self.context_menu.add_command(label="Download", command=self.option1)
        self.context_menu.add_command(label="Option 2", command=self.option2)
        # ... Add more options as needed ...

    def on_right_click(self, event):
        print("Right-click event triggered")  # Debugging line
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()


    def option2(self):
        print("Option 2 selected")
        # ... Implement functionality for Option 2 ...



    def option1(self):
        selected_items = self.user_tree.selection()
        access_token = get_config_item('access_token')
        selected_user_email = self.user_combobox.get()  # Get the selected user's email

        for item_id in selected_items:
            if item_id in self.download_link_map:
                recording_details = self.download_link_map[item_id]

                filename, foldername = format_filename(recording_details, recording_details['file_type'], recording_details['file_extension'], recording_details['recording_type'], recording_details['id'])

                recording_start_str = recording_details['recording_start']  # Replace with your actual date string
                parsed_date = parse(recording_start_str)
                formatted_date = parsed_date.strftime('%b %Y').upper()

                folder = self.selected_folder_path +'/'+ formatted_date + '/' + str(parsed_date.day) + '/' + foldername
                # Ensure that the directory exists
                if not os.path.exists(folder):
                    os.makedirs(folder)
                                
                download_url = recording_details["download_url"]  + "?access_token=" + access_token
                
                self.download_queue.put((item_id, download_url, folder, filename))
                record_or_update_download_status(recording_details['host_id'], recording_details['id'], recording_details['meeting_id'], filename, download_url, 'attempted')


    def update_download_progress(self, item_id, progress):
        # Get the current values of the item
        current_values = list(self.user_tree.item(item_id, 'values'))

        if progress == 100:
            current_values[-1] = "Download Complete"
            status = 'complete'

        elif progress == -1:
            current_values[-1] = "Download Failed"
            status = 'failed'

        else:
            current_values[-1] = f"Downloading... {progress}%"
            status = 'downloading'

        # Update the item with new values
        self.user_tree.item(item_id, values=current_values)

        # Update the download record in the database
        recording_details = self.download_link_map.get(item_id, {})
        user_id = self.user_combobox.get()  # Assuming this returns the user ID
        update_download_record(recording_details.get('recording_id', ''), status)

    def start_download_worker(self):
        def worker():
            while True:
                item_id, url, destination_folder, file_name = self.download_queue.get()
                download_file(url, destination_folder, file_name, item_id, lambda fn, p: self.update_download_progress(item_id, p)) 
                # Delay for 25 seconds after the download is complete
                time.sleep(25)
                self.download_queue.task_done()

        threading.Thread(target=worker, daemon=True).start()

    def view_download(self):
        download_data = get_download_history()

        for record in download_data:
            print(record)


    def load_default_settings(self):
        # Fetch and insert default client ID
        download_folder_path = get_config_item('download_folder_path')

        if download_folder_path:
            self.selected_folder_path = download_folder_path  # Store the selected folder path
            self.selected_folder_label.config(text="Selected Folder: {}".format(download_folder_path))

 

    def start_download_schedule(self):
        download_time = self.download_time_entry.get()
        self.download_task
        
        # Validate download_time format here if necessary

        # Clear existing schedule
        schedule.clear()

        # Schedule the task
        schedule.every().day.at(download_time).do(self.download_task)

        # Start the scheduler in a separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)

        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()

        print(f"Download scheduled at {download_time} every day")

    def download_task(self):
        all_meetings = []
        users = get_all_users()
        print(users)
        # Get today's date
        today_date = datetime.now()

        # Subtract one day to get yesterday's date
        yesterday_date = today_date - timedelta(days=1)

        end_date = today_date.strftime("%Y-%m-%d")
        start_date = yesterday_date.strftime("%Y-%m-%d")

        for user in users:
            # Use logging instead of print in production code
            meetings = fetch_user_recordings(user.display_name, start_date, end_date)
            all_meetings.extend(meetings)

        self.populate_meetings_in_treeview(all_meetings)

        access_token = get_config_item('access_token')
        for item_id, recording_details in self.download_link_map.items():
                recording_details = self.download_link_map[item_id]

                filename, foldername = format_filename(recording_details, recording_details['file_type'], recording_details['file_extension'], recording_details['recording_type'], recording_details['id'])

                recording_start_str = recording_details['recording_start']  # Replace with your actual date string
                parsed_date = parse(recording_start_str)
                formatted_date = parsed_date.strftime('%b %Y').upper()

                folder = self.selected_folder_path +'/'+ formatted_date + '/' + str(parsed_date.day) + '/' + foldername
                # Ensure that the directory exists
                if not os.path.exists(folder):
                    os.makedirs(folder)

                download_url = recording_details["download_url"]  + "?access_token=" + access_token
                
                self.download_queue.put((item_id, download_url, folder, filename))
                record_or_update_download_status(recording_details['host_id'], recording_details['id'], recording_details['meeting_id'], filename, download_url, 'attempted')


def format_filename(recording, file_type, file_extension, recording_type, recording_id):
    topic = recording['meeting_topic'].replace('/', '&')
    rec_type = recording_type.replace("_", " ").title()
    meeting_time = parse(recording['recording_start']).strftime('%Y.%m.%d - %I.%M %p UTC')
    return '{} - {} - {}.{}'.format(
        meeting_time, topic+" - "+rec_type, recording_id, file_extension.lower()),'{} - {}'.format(topic, meeting_time)
    
    

