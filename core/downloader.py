# core/downloader.py
import requests
import os
import threading
from datetime import datetime
from db.database import delete_all_users, record_download, get_download_history,  update_download_record, record_or_update_download_status, check_download_status, upsert_config_item,delete_config_item, get_all_users
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

def download_file(url, destination_folder, file_name, item_id, update_callback):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # This will raise an exception for HTTP error codes

        # Get the total length of the file from the headers
        total_length = response.headers.get('content-length')

        if total_length is None:  # No content length header
            update_callback(item_id, 100)  # Directly mark as 100% if no content length
        else:
            # Initialize download progress variables
            dl = 0
            total_length = int(total_length)

            # Open a file in write-binary mode to write the downloaded content
            with open(os.path.join(destination_folder, file_name), 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        dl += len(chunk)
                        file.write(chunk)

                        # Calculate and update download progress
                        done = int(100 * dl / total_length)
                        update_callback(item_id, done)
            
            # Mark download as complete
            update_callback(item_id, 100)

    except Exception as e:
        # Log the error and update the callback with failure
        print(f"An error occurred during download: {e}")
        update_callback(item_id, -1)


                       
# def start_download_file_all():

#     print('disini kita mahu start download')
#     users = populate_user_list()
#     start_date = start_date_entry.get()
#     end_date = end_date_entry.get()
#     for email, user_id, first_name, last_name in users:
#         print(color.BOLD + "\nGetting recording list for {} {} ({})".format(first_name,
#                                                                             last_name, email) + color.END)
#         # wait n.n seconds so we don't breach the API rate limit
#         # time.sleep(0.1)
#         recordings = list_recordings(user_id, start_date, end_date)
#         total_count = len(recordings)
#         print("==> Found {} recordings".format(total_count))

#         for index, recording in enumerate(recordings):
#             success = False
#             meeting_id = recording['uuid']
#             if meeting_id in COMPLETED_MEETING_IDS:
#                 print("==> Skipping already downloaded meeting: {}".format(meeting_id))
#                 continue

#             downloads = get_downloads(recording)
#             for file_type, file_extension, download_url, recording_type, recording_id in downloads:
#                 if recording_type != 'incomplete':
#                     filename, foldername = format_filename(
#                         recording, file_type, file_extension, recording_type, recording_id)
#                     # truncate URL to 64 characters
#                     truncated_url = download_url[0:64] + "..."
#                     print("==> Downloading ({} of {}) as {}: {}: {}".format(
#                         index+1, total_count, recording_type, recording_id, truncated_url))
#                     success |= download_recording(download_url, email, filename, foldername)
#                     success = True
#                 else:
#                     print("### Incomplete Recording ({} of {}) for {}".format(index+1, total_count, recording_id))
#                     success = False
#             if success:
#                 # if successful, write the ID of this recording to the completed file
#                 with open(COMPLETED_MEETING_IDS_LOG, 'a') as log:
#                     COMPLETED_MEETING_IDS.add(meeting_id)
#                     log.write(meeting_id)
#                     log.write('\n')
#                     log.flush()
#     print(color.BOLD + color.GREEN + "\n*** All done! ***" + color.END)
#     save_location = os.path.abspath(DOWNLOAD_DIRECTORY)
#     print(color.BLUE + "\nRecordings have been saved to: " +
#           color.UNDERLINE + "{}".format(save_location) + color.END + "\n")