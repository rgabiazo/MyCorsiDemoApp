import csv
from datetime import datetime
import os
from kivy.app import App
from kivy.utils import platform

class DataHandler:
    """Class to handle participant data."""

    def __init__(self, participant_id, session_name, session_type):
        self.participant_id = participant_id
        self.session_name = session_name
        self.session_type = session_type

    def save_task_data(self, data_recorder_data):

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.session_type}-{self.participant_id}-{self.session_name}_{timestamp}.csv"

        # Determine the file path based on platform
        if platform == 'ios':
            # For iOS devices (iPad)
            # Save the file to the app's Documents directory
            from plyer import storagepath
            documents_dir = storagepath.get_documents_dir()
            # Strip any "file://" prefix if present:
            if documents_dir.startswith("file://"):
                documents_dir = documents_dir.replace("file://", "")

            # Ensure the directory exists
            if not os.path.exists(documents_dir):
                os.makedirs(documents_dir)

            filepath = os.path.join(documents_dir, filename)

        else:
            # For desktop or other platforms
            # Save to 'CorsiData' folder in the current directory
            current_dir = os.getcwd()
            data_dir = os.path.join(current_dir, 'CorsiData')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            filepath = os.path.join(data_dir, filename)

        # Define the headers for the CSV file
        header = [
            'Participant_ID', 'Session_Name', 'Session_Type', 'Task_Mode',
            'Sequence_Length', 'Trial_Number', 'Correct_Sequence',
            'Button_Presses', 'Reaction_Times', 'Reaction_Times_Average',
            'Max_Sequence_Length', 'Accuracy'
        ]

        # Open the CSV file and write data
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            # Grab the final forward/backward max from data_recorder_data
            max_forward = data_recorder_data.get('forward_max_sequence_length', None)
            max_backward = data_recorder_data.get('backward_max_sequence_length', None)

            # Process each key in data_recorder_data
            for key, value in data_recorder_data.items():
                # Skip max_sequence_length so they're not treated as trials
                if key in ('forward_max_sequence_length', 'backward_max_sequence_length'):
                    continue

                # key is like 'forward_sequence_length_2'
                parts = key.split('_')
                task_mode = parts[0]  # 'forward' or 'backward'
                sequence_length = parts[-1]  # Length as string

                # Iterate over trials
                num_trials = len(value['current_sequence'])
                for i in range(num_trials):
                    trial_number = i + 1  # Starting from 1

                    correct_sequence = value['current_sequence'][i]
                    button_presses = value['button_presses'][i]
                    reaction_times = value['reaction_times'][i]

                    # Calculate accuracy
                    accuracy = 1 if correct_sequence == button_presses else 0

                    # Convert lists to strings
                    correct_sequence_str = ','.join(map(str, correct_sequence))
                    button_presses_str = ','.join(map(str, button_presses))
                    reaction_times_str = ','.join(f"{rt:.4f}" for rt in reaction_times)

                    # Compute average reaction time
                    if reaction_times:
                        avg_rt = sum(reaction_times) / len(reaction_times)
                    else:
                        avg_rt = 0.0
                    avg_rt_str = f"{avg_rt:.4f}"

                    # Decide if this row should contain the max sequence length
                    if (
                        task_mode == 'forward'
                        and i == num_trials - 1
                        and max_forward is not None
                        and int(sequence_length) == max_forward
                    ):
                        max_seq_len_str = str(max_forward)
                    elif (
                        task_mode == 'backward'
                        and i == num_trials - 1
                        and max_backward is not None
                        and int(sequence_length) == max_backward
                    ):
                        max_seq_len_str = str(max_backward)
                    else:
                        max_seq_len_str = ''  # leave blank for other rows

                    # Prepare data row
                    data_row = [
                        self.participant_id,
                        self.session_name,
                        self.session_type,
                        task_mode,
                        sequence_length,
                        trial_number,
                        correct_sequence_str,
                        button_presses_str,
                        reaction_times_str,
                        avg_rt_str,
                        max_seq_len_str,
                        accuracy
                    ]

                    writer.writerow(data_row)

        print(f"Data saved to {filepath}")