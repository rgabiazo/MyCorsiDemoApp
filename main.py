from kivy.app import App
from kivy.lang import Builder
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from datahandler import DataHandler
from kivy.core.text import LabelBase
from kivy.graphics import Color, RoundedRectangle

import os
import time



#  Fonts/Icons (fontello.ttf) in 'fonts' directory
LabelBase.register(name='Fontello',
                   fn_regular=os.path.join('fonts', 'fontello.ttf'))

#  Fonts/Icons (helvetica.ttf) in 'fonts' directory
LabelBase.register(
    name="Helvetica",  # Text font
    fn_regular=os.path.join("fonts", "helvetica.ttf"))

# Function to get instruction text based on task mode
def get_instruction_text(task_mode):
    if task_mode == 'forward':
        order_phrase = 'in [u][i]the same order[/i][/u]'
    elif task_mode == 'backward':
        order_phrase = 'in [u][i]backward order[/i][/u]'
    else:
        return "Invalid task mode."

    instruction_text = (
        "\nIn this task, you will see nine [color=0000FF]BLUE[/color] blocks on the screen. For each trial, "
        "a sequence of blocks will turn [color=FF0000]RED[/color] one by one. Your task is to remember the "
        "order in which the blocks light up and then repeat the sequence {order_phrase} "
        "by tapping on the blocks.\n\n"
        "The sequences will start short and will gradually get longer, making it more "
        "difficult to remember the order.\n\n"
        "Try to recall as many sequences correctly as you can.\n\n"
        "There is no time limit for each trial, but please try to respond as quickly "
        "and accurately as possible.\n\n"
        "You will first do two practice trials. When you are ready to practice the "
        'task, tap the "Start" button below to begin.'
    ).format(order_phrase=order_phrase)

    return instruction_text

# Touch class to handle opacity on click events for widgets
class Touch(Widget):
    """A widget that changes opacity on touch events."""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.opacity = 0.5
        return super(Touch, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.opacity = 1
        return super(Touch, self).on_touch_up(touch)

class TouchSpinner(Spinner):
    """A Spinner widget that handles touch events without changing opacity."""

    def on_touch_down(self, touch):
        return super(TouchSpinner, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        return super(TouchSpinner, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        return super(TouchSpinner, self).on_touch_up(touch)

class TouchTextInput(TextInput): # Can add print statements here for debugging
    """A TextInput widget that handles touch events without changing opacity."""

    def on_touch_down(self, touch):
        return super(TouchTextInput, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        return super(TouchTextInput, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        return super(TouchTextInput, self).on_touch_up(touch)


# Custom Button that incorporates Touch functionality
class TouchButton(Button):
    """A Button that changes opacity when touched."""

    def __init__(self, **kwargs):
        super(TouchButton, self).__init__(**kwargs)
        self.bind(state=self.on_state_change)

    def on_state_change(self, instance, value):
        self.opacity = 0.5 if value == 'down' else 1

class PopupButton(TouchButton):
    """A Python class so that 'PopupButton' can be referenced in code."""
    pass

class BlockButton(Button):
    """A Button widget specifically for blocks, handling color changes on touch events."""

    def __init__(self, **kwargs):
        super(BlockButton, self).__init__(**kwargs)
        self.grabbed = False
        self.parent_screen = None  # Will be set when creating the block
        self.number = None  # Block number

    def on_touch_down(self, touch):
        if not self.parent_screen.task_handler.user_can_interact:
            return False  # Ignore touch events if user cannot interact
        if self.collide_point(*touch.pos):
            # Change color to bright red
            self.background_color = (1, 0, 0, 1)  # Bright red color
            self.grabbed = True
            # Consume the touch event
            return True
        return super(BlockButton, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.grabbed:
            # Change color back to blue
            self.background_color = (0, 0, 1, 1)  # Blue color
            self.grabbed = False
            # Record the block press
            if self.parent_screen and self.parent_screen.task_handler:
                self.parent_screen.task_handler.on_block_press(self.number)
            # Consume the touch event
            return True
        return super(BlockButton, self).on_touch_up(touch)

# Base class for popups that handles font resizing and window event binding
class ResponsivePopup(Popup):
    """Base class for popups that require responsive font resizing."""

    def __init__(self, **kwargs):
        super(ResponsivePopup, self).__init__(**kwargs)
        self._font_widgets = []  # List to keep track of widgets that need font resizing

    def add_font_widget(self, widget, font_size_ratio=0.02):
        """Adds a widget to the list of widgets that require font resizing."""
        self._font_widgets.append((widget, font_size_ratio))
        widget.font_size = Window.width * font_size_ratio

    def bind_font_size(self):
        """Binds the window resize event to the font size update method."""
        Window.bind(size=self.update_font_sizes)

    def unbind_font_size(self):
        """Unbinds the window resize event from the font size update method."""
        Window.unbind(size=self.update_font_sizes)

    def update_font_sizes(self, instance, value):
        """Updates the font sizes of registered widgets based on window width."""
        for widget, ratio in self._font_widgets:
            widget.font_size = Window.width * ratio

    def open(self, *args, **kwargs):
        """Overrides the open method to bind font size updates."""
        super(ResponsivePopup, self).open(*args, **kwargs)
        self.bind_font_size()

    def dismiss(self, *args, **kwargs):
        """Overrides the dismiss method to unbind font size updates."""
        self.unbind_font_size()
        super(ResponsivePopup, self).dismiss(*args, **kwargs)


class InstructionsPopup(ResponsivePopup):
    def __init__(self, task_mode='forward', **kwargs):
        super().__init__(**kwargs)

        self.title = "Instructions"  # or set in KV
        # self.size_hint = (0.9, 0.9)  # if not set in KV

        instruction_text = get_instruction_text(task_mode)

        # Layout for label + scrollview + start button
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # The instructions_label with color markup (BLUE/RED)
        self.instructions_label = Label(
            text=instruction_text,
            size_hint_y=None,
            markup=True,       # allows [color=] etc.
            halign='left',
            valign='top',
            color=(0, 0, 0, 1),
            font_name="Helvetica"
        )

        # Let the label scale
        self.add_font_widget(self.instructions_label, font_size_ratio=0.02)

        # Dynamically set label height to match its content
        self.instructions_label.bind(
            width=lambda *_: self.instructions_label.setter('text_size')(
                self.instructions_label, (self.instructions_label.width, None)
            ),
            texture_size=lambda *_: self.instructions_label.setter('height')(
                self.instructions_label, self.instructions_label.texture_size[1]
            )
        )

        scroll_view = ScrollView(size_hint=(1, 0.9))
        scroll_view.add_widget(self.instructions_label)
        content.add_widget(scroll_view)

        # "Start" button with a fixed dp font size:
        start_button = PopupButton(
            text='Start',
            size_hint=(1, 0.1),
            font_name="Helvetica",
            font_size=dp(24)   # <-- keeps text from shrinking on a big screen
        )
        content.add_widget(start_button)
        start_button.bind(on_release=self.start_pressed)

        # Instead of self.content = content, add to the BoxLayout from KV
        instructions_box = self.ids.instructions_box
        instructions_box.add_widget(content)

    def start_pressed(self, instance):
        """Close the popup and go to the next step."""
        self.dismiss()
        app = App.get_running_app()
        if app.root.current == "main":
            app.root.current = "ready"
            app.root.transition.direction = "left"
        else:
            second_window = app.root.get_screen('second')
            second_window.start_practice_task()

class MainWindow(Screen):
    """Screen class for the main participant info entry window."""

    def validate_and_proceed(self):
        """Validates input fields and proceeds accordingly."""
        participant_id = self.ids.participantID.text.strip()
        session_name = self.ids.session_name.text.strip()
        session_type = self.ids.session_type_spinner.text.strip()

        # Check for spaces in 'Participant ID' and 'Session Name'
        if ' ' in participant_id or ' ' in session_name:
            # Show popup 'Please ensure there are no spaces'
            self.show_popup('Please ensure there are no spaces.')
        # Check if any fields are blank or 'Session Type' is not selected
        elif not participant_id or not session_name or session_type == 'Select Session Type':
            # Show popup 'Please complete all fields: Participant ID, Session Name, and Session Type.'
            self.show_popup('Please complete all fields: Participant ID, Session Name, and Session Type.')
        else:
            # All criteria are met
            # Process the data
            participant_id_processed = participant_id
            session_name_processed = 'ses-' + session_name
            session_type_processed = session_type.replace(' ', '-')

            # Send data to datahandler
            data_handler = DataHandler(participant_id_processed, session_name_processed, session_type_processed)

            # Store the data_handler instance in the app
            app = App.get_running_app()
            app.data_handler = data_handler

            # Clear text boxes and reset spinner
            self.ids.participantID.text = ''
            self.ids.session_name.text = ''
            self.ids.session_type_spinner.text = 'Select Session Type'

            # Open InstructionsPopup
            instructions_popup = InstructionsPopup(task_mode='forward')
            instructions_popup.open()

    def show_popup(self, message):
        """Displays a popup with the given message."""
        popup = ErrorPopup(message_text=message)
        popup.open()

    def show_exit_popup(self, *args):
        """Shows a popup asking if the user wants to exit the app."""

        def on_ok():
            # For instance, actually stop the app:
            App.get_running_app().stop()

        popup = ExitConfirmationPopup(ok_callback=on_ok)
        popup.open()

class DataRecorder:
    """Class to record the blocks pressed and reaction times."""

    def __init__(self):
        self.data = {}

    def record_sequence(self, sequence_length, current_sequence, button_presses, reaction_times, task_mode):
        key = f"{task_mode}_sequence_length_{sequence_length}"
        if key not in self.data:
            self.data[key] = {'current_sequence': [], 'button_presses': [], 'reaction_times': []}
        self.data[key]['current_sequence'].append(current_sequence)
        self.data[key]['button_presses'].append(button_presses)
        self.data[key]['reaction_times'].append(reaction_times)

    def reset(self):
        self.data = {}

class BlockSetup:
    """Class to handle setting up the blocks in the given layout with predefined positions."""

    def __init__(self, parent_layout, parent_screen):
        self.parent_layout = parent_layout
        self.parent_screen = parent_screen  # Reference to SecondWindow instance
        self.setup_blocks()

    def setup_blocks(self):
        """Sets up the blocks in the parent_layout with predefined positions."""

        # Define the board dimensions
        board_width_mm = 255
        board_height_mm = 205

        # Define the size_hint for the blocks relative to the board
        square_size_mm = 30

        # size_hint for blocks relative to board_layout
        block_size_hint_x = square_size_mm / board_width_mm
        block_size_hint_y = square_size_mm / board_height_mm

        block_size_hint = (block_size_hint_x, block_size_hint_y)

        # List of squares with predefined positions
        squares = [
            {'number': 1, 'x_mm': 130, 'y_mm': 155},
            {'number': 2, 'x_mm': 30, 'y_mm': 145},
            {'number': 3, 'x_mm': 180, 'y_mm': 120},
            {'number': 4, 'x_mm': 70, 'y_mm': 110},
            {'number': 5, 'x_mm': 140, 'y_mm': 90},
            {'number': 6, 'x_mm': 195, 'y_mm': 60},
            {'number': 7, 'x_mm': 15, 'y_mm': 50},
            {'number': 8, 'x_mm': 75, 'y_mm': 20},
            {'number': 9, 'x_mm': 135, 'y_mm': 30},
        ]

        # Create blocks at predefined positions
        for square in squares:
            x_mm = square['x_mm']
            y_mm = square['y_mm']

            # Compute pos_hint relative to board dimensions
            pos_hint_x = x_mm / board_width_mm
            pos_hint_y = y_mm / board_height_mm

            pos_hint = {'x': pos_hint_x, 'y': pos_hint_y}

            # Create the block as a BlockButton
            block = BlockButton(
                background_normal='',
                background_color=(0, 0, 1, 1),  # Blue color
                size_hint=block_size_hint,
                pos_hint=pos_hint,
            )

            # Store the block number and parent_screen
            block.number = square['number']
            block.parent_screen = self.parent_screen

            # Add the block to the parent_layout
            self.parent_layout.add_widget(block)

            # Store the block in parent_screen's blocks dictionary
            self.parent_screen.blocks[square['number']] = block

class BoardLayout(FloatLayout):
    """Custom layout to maintain aspect ratio of the board."""
    pass  # No changes needed here

class PracticeCompletePopup(ResponsivePopup):
    def __init__(self, parent_screen, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen

        practice_box = self.ids.practice_box  # The BoxLayout from KV

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        message_text = (
            "The practice trials are now complete.\n\n"
            "As a reminder, please try to respond as quickly and accurately as possible for each trial.\n\n"
            'When you are ready to begin the task, tap the "Start" button.'
        )

        self.message_label = Label(
            text=message_text,
            size_hint_y=None,
            halign='left',
            valign='top',
            font_name="Helvetica",
            color=(0, 0, 0, 1),
        )

        self.add_font_widget(self.message_label, font_size_ratio=0.02)

        # Let the label adapt to its content
        self.message_label.bind(
            width=lambda *_: setattr(
                self.message_label, 'text_size', (self.message_label.width, None)
            ),
            texture_size=lambda *_: setattr(
                self.message_label, 'height', self.message_label.texture_size[1]
            )
        )

        scroll_view = ScrollView(size_hint=(1, 0.8))
        scroll_view.add_widget(self.message_label)
        content.add_widget(scroll_view)

        # Create the button with a fixed dp font size
        start_button = PopupButton(
            text='Start',
            size_hint=(1, 0.2),
            font_name="Helvetica",
            font_size=dp(24)  # <--- The key line so it doesn't shrink
        )
        content.add_widget(start_button)

        # Hook up the button action
        start_button.bind(on_release=self.start_pressed)

        # Finally, add to the parent layout
        practice_box.add_widget(content)

    def start_pressed(self, instance):
        self.dismiss()
        self.parent_screen.task_handler = TrialTask(self.parent_screen, self.parent_screen.trial_sequences)
        self.parent_screen.task_handler.start_next_sequence()


class BaseMessagePopup(ResponsivePopup):
    """A base popup with a white, rounded background from KV."""

    def __init__(self, message_text, button_text, button_callback, size_hint=(0.9, 0.9), **kwargs):
        super(BaseMessagePopup, self).__init__(**kwargs)

        # If you want to override the default size from KV:
        self.size_hint = size_hint

        # Build the layout for label + button in code
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Label (with your resizing logic)
        self.message_label = Label(
            text=message_text,
            size_hint_y=None,
            halign='center',
            valign='middle',
            font_name="Helvetica",
            color=(0, 0, 0, 1)
        )
        self.add_font_widget(self.message_label, font_size_ratio=0.02)
        self.message_label.bind(
            width=lambda *_: self.message_label.setter('text_size')(
                self.message_label, (self.message_label.width, None)
            ),
            texture_size=lambda *_: self.message_label.setter('height')(
                self.message_label, self.message_label.texture_size[1]
            )
        )
        scroll_view = ScrollView(size_hint=(1, 0.8))
        scroll_view.add_widget(self.message_label)
        layout.add_widget(scroll_view)

        # Button
        action_button = PopupButton(
            text=button_text,
            size_hint=(1, 0.1),
            font_name="Helvetica"
        )
        action_button.bind(on_release=button_callback)
        layout.add_widget(action_button)

        # Store in self._layout, not self.content
        self._layout = layout

        # Attach self._layout to the BoxLayout from KV
        main_box = self.ids.main_box
        main_box.add_widget(self._layout)
        # Done. The popup sees only one top-level child: main_box



# Add this class below BaseMessagePopup
class ErrorPopup(BaseMessagePopup):
    """Popup class to display error messages."""

    def __init__(self, message_text, **kwargs):
        super().__init__(
            message_text=message_text,
            button_text='OK',
            button_callback=self.dismiss_popup,
            size_hint=(0.6, 0.4),
            **kwargs
        )

    def dismiss_popup(self, instance):
        self.dismiss()

class CompletionPopup(BaseMessagePopup):
    """Popup for 'task complete' using the same white, rounded background."""

    def __init__(self, parent_screen, **kwargs):
        self.parent_screen = parent_screen
        super().__init__(
            message_text="\nThank you! The task is now completed.\n\nPlease let the researcher know.",
            button_text="Ok",
            button_callback=self.exit_pressed,
            size_hint=(0.6, 0.6),
            **kwargs
        )

    def exit_pressed(self, instance):
        """Dismiss the popup, maybe switch to the next step."""
        self.dismiss()
        self.parent_screen.task_mode = 'backward'
        # show next instructions if needed

        backward_instructions_popup = InstructionsPopup(task_mode='backward')
        backward_instructions_popup.open()

class FinalCompletionPopup(BaseMessagePopup):
    """Popup class to display the final task completion message."""

    def __init__(self, parent_screen, **kwargs):
        self.parent_screen = parent_screen
        super().__init__(
            message_text="\nThank you! The task is now completed.\n\nPlease let the researcher know.",
            button_text="Exit",
            button_callback=self.exit_pressed,
            size_hint=(0.6, 0.6),
            **kwargs
        )

    def exit_pressed(self, instance):
        """When 'Exit' button is pressed."""
        self.dismiss()
        # Typically, do final cleanup or navigate away:
        self.parent_screen.exit_task()

class SequenceTask:
    """Base class for handling sequence tasks."""

    def __init__(self, parent_screen):
        self.parent_screen = parent_screen
        self._user_can_interact = False
        self.blocks = parent_screen.blocks
        self.user_sequence = []
        self.current_sequence = []
        self.sequence_start_time = None
        self.block_press_times = []  # For reaction times per block

    @property
    def user_can_interact(self):
        return self._user_can_interact

    @user_can_interact.setter
    def user_can_interact(self, value):
        self._user_can_interact = value
        if self.parent_screen:
            if value:
                self.parent_screen.show_done_button()
            else:
                self.parent_screen.hide_done_button()

    def start_sequence(self, sequence):
        """Starts the given block sequence."""
        self.current_sequence = sequence
        self.user_can_interact = False
        self.user_sequence = []
        self.block_press_times = []

        # Show 'Ready' label
        self.show_ready()
        total_delay = 3  # Delay after 'Ready'

        # Schedule block sequences
        for i, block_number in enumerate(sequence):
            Clock.schedule_once(lambda dt, bn=block_number: self.light_up_block(bn), total_delay)
            total_delay += 1  # Block stays lit for 1 second
            Clock.schedule_once(lambda dt, bn=block_number: self.turn_off_block(bn), total_delay)
            total_delay += 1  # Wait 1 second before next block

        # After the sequence is done, schedule the user's turn to start
        Clock.schedule_once(self.start_user_turn, total_delay)

    def show_ready(self):
        # Show 'Ready' label and overlay
        self.ready_label = Label(
            text='Ready',
            font_size=Window.width * 0.05,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            font_name="Helvetica"
        )
        self.overlay = FloatLayout()
        with self.overlay.canvas:
            Color(0, 0, 0, 0.5)
            Rectangle(pos=self.parent_screen.pos, size=self.parent_screen.size)
        self.overlay.add_widget(self.ready_label)
        self.parent_screen.add_widget(self.overlay)
        # Schedule to remove overlay after 1 second
        Clock.schedule_once(self.remove_ready_overlay, 1)

    def remove_ready_overlay(self, dt):
        self.parent_screen.remove_widget(self.overlay)

    def light_up_block(self, block_number):
        """Lights up the specified block."""
        block = self.blocks[block_number]
        block.background_color = (1, 0, 0, 1)  # Red color

    def turn_off_block(self, block_number):
        """Turns off the specified block."""
        block = self.blocks[block_number]
        block.background_color = (0, 0, 1, 1)  # Blue color

    def start_user_turn(self, dt):
        """Notifies the user that it's their turn and allows interaction."""
        # Show 'Your turn' label and overlay
        self.your_turn_label = Label(
            text='Your turn',
            font_size=Window.width * 0.05,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            font_name="Helvetica"
        )
        self.overlay = FloatLayout()
        with self.overlay.canvas:
            Color(0, 0, 0, 0.5)
            Rectangle(pos=self.parent_screen.pos, size=self.parent_screen.size)
        self.overlay.add_widget(self.your_turn_label)
        self.parent_screen.add_widget(self.overlay)
        # Schedule to remove overlay after 1 second
        Clock.schedule_once(self.remove_your_turn_overlay, 1)

    def remove_your_turn_overlay(self, dt):
        self.parent_screen.remove_widget(self.overlay)
        self.user_can_interact = True
        self.sequence_start_time = time.time()

    def on_block_press(self, block_number):
        if self.user_can_interact:
            self.user_sequence.append(block_number)
            # Record the time since 'Your turn' started
            press_time = time.time() - self.sequence_start_time
            self.block_press_times.append(press_time)

    def get_correct_sequence(self):
        """Returns the correct sequence to compare with user's input."""
        if self.parent_screen.task_mode == 'forward':
            return self.current_sequence
        elif self.parent_screen.task_mode == 'backward':
            return list(reversed(self.current_sequence))
        else:
            return self.current_sequence

    def check_user_sequence(self):
        pass  # To be implemented in subclasses

class PracticeTask(SequenceTask):
    def __init__(self, parent_screen, sequences):
        super().__init__(parent_screen)
        self.sequences = sequences
        self.current_index = 0

    def start_next_sequence(self):
        if self.current_index < len(self.sequences):
            sequence = self.sequences[self.current_index]
            self.start_sequence(sequence)
        else:
            # Practice is over
            self.parent_screen.show_practice_complete_popup()

    def check_user_sequence(self):
        self.user_can_interact = False  # Disable interaction
        correct_sequence = self.get_correct_sequence()
        if self.user_sequence == correct_sequence:
            # Correct
            self.parent_screen.show_correct()
            Clock.schedule_once(self.next_sequence, 1)
        else:
            # Incorrect
            self.parent_screen.show_try_again()
            # Reset user's sequence and timings
            self.user_sequence = []
            self.block_press_times = []

    def next_sequence(self, dt):
        self.current_index += 1
        self.start_next_sequence()

class TrialTask(SequenceTask):
    """Class for handling the main trial sequences."""

    def __init__(self, parent_screen, sequences):
        super().__init__(parent_screen)
        self.sequences = sequences
        self.current_index = 0
        self.incorrect_attempts = 0  # Number of incorrect attempts at current sequence length
        self.current_sequence_length = 0  # Track the current sequence length
        self.data_recorder = parent_screen.data_recorder

    def start_next_sequence(self):
        if self.current_index < len(self.sequences):
            sequence = self.sequences[self.current_index]
            sequence_length = len(sequence)
            # Check if sequence length has changed
            if sequence_length != self.current_sequence_length:
                # Reset incorrect_attempts when sequence length changes
                self.incorrect_attempts = 0
                self.current_sequence_length = sequence_length
            self.start_sequence(sequence)
        else:

            # Done with either forward or backward
            # Store the final max sequence length into DataRecorder
            if self.parent_screen.task_mode == 'forward':
                self.parent_screen.data_recorder.data['forward_max_sequence_length'] = self.current_sequence_length
            else:
                self.parent_screen.data_recorder.data['backward_max_sequence_length'] = self.current_sequence_length

            # All sequences completed
            self.parent_screen.show_completion_popup()

    def check_user_sequence(self):
        self.user_can_interact = False  # Disable interaction

        # Record data
        sequence_length = len(self.current_sequence)
        task_mode = self.parent_screen.task_mode

        # Get the sequence to store
        if task_mode == 'forward':
            current_sequence_to_store = self.current_sequence.copy()
        elif task_mode == 'backward':
            current_sequence_to_store = list(reversed(self.current_sequence))
        else:
            current_sequence_to_store = self.current_sequence.copy()

        self.data_recorder.record_sequence(
            sequence_length, current_sequence_to_store, self.user_sequence.copy(), self.block_press_times.copy(), task_mode
        )

        correct_sequence = self.get_correct_sequence()

        if self.user_sequence == correct_sequence:
            # Correct sequence
            self.incorrect_attempts = 0  # Reset incorrect attempts
            self.current_index += 1
            self.start_next_sequence()
        else:
            # Incorrect sequence
            self.incorrect_attempts += 1
            if self.incorrect_attempts >= 2:
                # Two incorrect sequences at this length; end task

                # Two incorrect sequences at this length; end task now
                # Store final max sequence length (i.e., last sequence done)
                if self.parent_screen.task_mode == 'forward':
                    self.parent_screen.data_recorder.data['forward_max_sequence_length'] = self.current_sequence_length
                else:
                    self.parent_screen.data_recorder.data['backward_max_sequence_length'] = self.current_sequence_length

                self.parent_screen.show_completion_popup()
            else:
                # Move to the next sequence
                self.current_index += 1
                self.start_next_sequence()


class ExitConfirmationPopup(Popup):
    """
    Custom popup class for confirming an exit action.
    Handle the 'OK' press.
    """
    def __init__(self, ok_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.ok_callback = ok_callback

    def on_ok_pressed(self):
        """
        Called when the user presses the 'OK' button.
        """
        if self.ok_callback:
            self.ok_callback()
        self.dismiss()

class SecondWindow(Screen):
    """Screen class for the secondary window that users navigate to."""

    def __init__(self, **kwargs):
        super(SecondWindow, self).__init__(**kwargs)
        self.data_recorder = DataRecorder()
        self.practice_sequences = [[1, 3], [1, 2, 3]]  # Practice trial sequences

        # Actual sequences during trials
        self.trial_sequences = [
            [8, 5],
            [6, 4],
            [4, 7, 2],
            [8, 1, 5],
            [3, 4, 1, 7],
            [6, 1, 5, 8],
            [5, 2, 1, 8, 6],
            [4, 2, 7, 3, 1],
            [3, 9, 2, 4, 8, 7],
            [3, 7, 8, 2, 9, 4],
            [5, 9, 1, 7, 4, 2, 8],
            [5, 7, 9, 2, 8, 4, 6],
            [5, 8, 1, 9, 2, 6, 4, 7],
            [5, 9, 3, 6, 7, 2, 4, 3],
            [5, 3, 8, 7, 1, 2, 4, 6, 9],
            [4, 2, 6, 8, 1, 7, 9, 3, 5]
        ]

        self.blocks = {}  # Stores blocks by number for easy access
        self.task_handler = None  # Will be set when the task starts
        self.task_mode = 'forward'  # 'forward' or 'backward'

        self.exit_popup = None  # Initialize to avoid AttributeError

    def on_enter(self):
        """Called when the screen is entered; sets up the blocks."""
        self.clear_widgets()

        # Reset data recorder
        self.data_recorder.reset()

        # Reset task_mode to 'forward'
        self.task_mode = 'forward'

        # Reset other variables
        self.blocks = {}  # Reinitialize blocks dictionary
        self.task_handler = None  # Ensure task handler is reset
        self.exit_popup = None  # Reset exit popup

        # Create the root layout as a FloatLayout
        main_layout = FloatLayout()
        self.add_widget(main_layout)

        # Create the 'Done' button with the custom DoneButton class
        self.done_button = DoneButton(
            text='Done',
            size_hint=(None, None),
            font_size='25dp',  # Adjust button font size here
            font_name="Helvetica",
            pos_hint={'right': 0.98, 'y': 0.02},  # Positioned at bottom-right with some margin
            opacity=0,
            disabled=True
        )
        self.done_button.bind(on_release=self.check_user_sequence)
        main_layout.add_widget(self.done_button)

        # Create the back button with the custom ExitButton class
        self.back_button = ExitButton(
            text=u'\ue800',  # Use the Unicode character code
            font_name='Fontello',  # Set the font to  registered font
            size_hint=(None, None),
            size=(dp(50), dp(50)),  # Adjust size as needed
            font_size='25dp',  #  Adjust the font size here
            pos_hint={'x': 0.02, 'top': 0.98}  # Positioned at top-left with some margin
        )
        self.back_button.bind(on_release=self.show_exit_popup)
        main_layout.add_widget(self.back_button)

        # Create an AnchorLayout to center the board_layout
        board_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        main_layout.add_widget(board_anchor)

        # Create the board_layout with size_hint set to None to control size manually
        self.board_layout = BoardLayout(size_hint=(None, None))
        board_anchor.add_widget(self.board_layout)

        # Bind to window size changes to update board size and button size
        Window.bind(size=self.update_layout_sizes)

        # Initial update of sizes
        self.update_layout_sizes()

        # Setup blocks within board_layout
        BlockSetup(self.board_layout, self)

        # Start the first practice sequence
        self.start_practice_task()


    def start_practice_task(self):
        """Starts the practice task depending on the task mode."""
        self.task_handler = PracticeTask(self, self.practice_sequences)
        self.task_handler.start_next_sequence()

    def update_layout_sizes(self, *args):
        """Updates the sizes of board_layout and buttons to maintain aspect ratio."""
        window_width, window_height = Window.size

        # Update 'Done' button size
        self.done_button.size = (window_width * 0.15, window_height * 0.08)

        # Update 'Back' button size
        self.back_button.size = (dp(50), dp(50))  # Keep a fixed size

        # Update board_layout size
        board_aspect_ratio = 255 / 205

        # Calculate maximum width and height for board_layout, considering some padding
        max_width = window_width * 0.9
        max_height = window_height * 0.9

        # Calculate board_layout size
        if max_width / board_aspect_ratio <= max_height:
            # Width is the limiting factor
            board_width = max_width
            board_height = board_width / board_aspect_ratio
        else:
            # Height is the limiting factor
            board_height = max_height
            board_width = board_height * board_aspect_ratio

        # Set the size of board_layout
        self.board_layout.size = (board_width, board_height)

    def on_leave(self):
        """Unbinds the window size when leaving the screen."""
        Window.unbind(size=self.update_layout_sizes)
        self.task_handler = None  # Reset the task handler

    def check_user_sequence(self, instance):
        """Checks the user's input sequence."""
        if self.task_handler:
            self.task_handler.check_user_sequence()

    def show_correct(self):
        """Shows 'Correct' message."""
        self.correct_label = Label(
            text='Correct',
            font_size=Window.width * 0.05,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            font_name="Helvetica"
        )
        self.add_widget(self.correct_label)
        # Schedule to remove the message after 1 second
        Clock.schedule_once(self.remove_correct_label, 1)

    def remove_correct_label(self, dt):
        """Removes the 'Correct' label from the screen."""
        self.remove_widget(self.correct_label)

    def show_try_again(self):
        """Shows 'Try again' message and restarts the practice sequence."""
        self.try_again_label = Label(
            text='Try again',
            font_size=Window.width * 0.05,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            font_name="Helvetica"

        )
        self.add_widget(self.try_again_label)
        # Schedule to remove the message after 1 second
        Clock.schedule_once(self.remove_try_again_label, 1)

    def remove_try_again_label(self, dt):
        """Removes the 'Try again' label from the screen."""
        self.remove_widget(self.try_again_label)
        # Restart the same practice sequence
        self.task_handler.start_sequence(self.task_handler.current_sequence)

    def show_practice_complete_popup(self):
        """Shows a popup indicating that practice trials are complete."""
        popup = PracticeCompletePopup(self)
        popup.open()

    def show_completion_popup(self):
        """Shows a popup indicating that the task is complete."""
        if self.task_mode == 'forward':
            popup = CompletionPopup(self)
            popup.open()
        else:
            # Task is over after backward trials
            popup = FinalCompletionPopup(self)
            popup.open()

    def show_exit_popup(self, *args):
        """Shows a popup asking if the user wants to exit."""
        if self.exit_popup:
            self.exit_popup.dismiss()
            self.exit_popup = None  # Reset exit_popup to None

        self.exit_popup = ExitConfirmationPopup(ok_callback=self.exit_task)
        self.exit_popup.open()

    def exit_task(self, *args):
        """Handles the exit process, saves data, and returns to main screen."""
        # Save data as needed
        self.save_data()

        # Close the popup if it exists
        if self.exit_popup:
            self.exit_popup.dismiss()
            self.exit_popup = None  # Reset exit_popup to None

        # Return to main window
        app = App.get_running_app()
        app.root.current = "main"
        app.root.transition.direction = "right"

    def save_data(self):
        """Saves the recorded data."""
        # Implement data saving logic here

        # Send data to datahandler
        app = App.get_running_app()
        if app.data_handler:
            app.data_handler.save_task_data(self.data_recorder.data)
        else:
            print("No DataHandler instance found.")

    def show_done_button(self):
        self.done_button.opacity = 1
        self.done_button.disabled = False

    def hide_done_button(self):
        self.done_button.opacity = 0
        self.done_button.disabled = True

# Add the ReadyWindow class
class ReadyWindow(Screen):
    """Screen that displays 'Ready' for 3 seconds before moving to the task."""

    def on_enter(self):
        """Called when the screen is entered; displays 'Ready' and transitions."""
        # Schedule the transition to 'second' screen after 3 seconds
        Clock.schedule_once(self.go_to_task, 3)

    def go_to_task(self, *args):
        """Transitions to the 'second' screen."""
        app = App.get_running_app()
        app.root.current = "second"
        app.root.transition.direction = "left"

    def on_leave(self):
        """Cancels the scheduled event if leaving before 3 seconds."""
        Clock.unschedule(self.go_to_task)

# Custom button classes for 'Done' and 'Exit' buttons
class DoneButton(TouchButton):
    """Custom button class for the 'Done' button with touch functionality."""
    pass

class ExitButton(TouchButton):
    """Custom button class for the 'Exit' button with touch functionality."""
    pass

# WindowManager to handle screen transitions and track global touch movements
class WindowManager(ScreenManager):
    """Manages screen transitions and captures touch movement across the screen."""

    def on_touch_move(self, touch):
        return super(WindowManager, self).on_touch_move(touch)

# Load the .kv file, which defines the UI layout
kv = Builder.load_file("my.kv")

# Main App class to run the Kivy app
class MyMainApp(App):
    """The main application class that loads and builds the UI."""
    def build(self):
        """Builds the app by returning the root widget from the .kv file."""
        self.data_handler = None  # Initialize data_handler to None
        return kv

# Entry point for the application
if __name__ == "__main__":
    MyMainApp().run()