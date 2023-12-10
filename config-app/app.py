import tkinter as tk
from tkinter import ttk
import serial
from serial.tools.list_ports import comports
from PIL import Image, ImageTk
import requests
from io import BytesIO

title = "Turntabler-App"


commands = {
    "start": b"r",
    "stop": b"s",
    "clockwise": b"c1",
    "counterclockwise": b"c0",
    "steps": b"t",
    "speed": b"v",
    "burn": b"b",
    "erase": b"e"
}

class ArduinoControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title(title)

        # Variables
        self.serial_port_var = tk.StringVar()
        self.clockwise_var = tk.BooleanVar()
        self.serial_ports = self.get_serial_ports()
        self.selected_port = None
        self.serial = None  # To store the serial port instance


        # GUI elements
        self.create_widgets()

        # Set up serial port reading
        self.setup_serial()

    def create_widgets(self):
        ### ROW 0
        # Headline
        headline_label = tk.Label(self.root, text=title, font=("Helvetica", 16))
        headline_label.grid(row=0, column=0, columnspan=5, pady=10)

        ### ROW 1
        # Headline
        headline_label = tk.Label(self.root, text="Arduino Port auswählen", font=("Helvetica", 10))
        headline_label.grid(row=2, column=0, columnspan=5, pady=10, sticky='w')

        ### ROW 3
        # Serial Port Dropdown
        serial_label = tk.Label(self.root, text="Select")
        serial_label.grid(row=3, column=0, pady=10)

        serial_dropdown = ttk.Combobox(self.root, textvariable=self.serial_port_var, values=self.serial_ports)
        serial_dropdown.grid(row=3, column=1, pady=10)
        serial_dropdown.set("Select Port")

        # Refresh Ports Button with Material Design refresh icon
        refresh_icon_url = "https://fonts.gstatic.com/s/i/materialicons/refresh/v10/24px.svg"
        refresh_icon_tk = self.get_material_design_icon(refresh_icon_url, (20, 20))

        if refresh_icon_tk:
            refresh_button = tk.Button(self.root, image=refresh_icon_tk, command=self.refresh_ports)
            refresh_button.image = refresh_icon_tk  # Keep a reference to prevent garbage collection
            refresh_button.grid(row=3, column=2, pady=10)
        else:
            refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh_ports)
            refresh_button.grid(row=3, column=2, pady=10)

        # Open/Close Serial Port Button
        self.open_close_button = tk.Button(self.root, text="Open Port", command=self.toggle_serial_port)
        self.open_close_button.grid(row=3, column=3, pady=10)

        ### ROW 4
        # Divider line
        divider = ttk.Separator(self.root, orient='horizontal')
        divider.grid(row=4, column=0, columnspan=5, sticky='ew', pady=10)

        ### ROW 5
        # Headline
        headline_label = tk.Label(self.root, text="Tilt-Modus", font=("Helvetica", 10))
        headline_label.grid(row=5, column=0, columnspan=5, pady=10, sticky='w')

        ### ROW 6

        # Input field for a number
        number_label = tk.Label(self.root, text="Schritte:")
        number_label.grid(row=6, column=0, pady=10)

        self.number_entry = tk.Entry(self.root, textvariable="Schwenkbereich")
        self.number_entry.grid(row=6, column=1, pady=10)

        # Button for triggering an action related to the entered number
        number_action_button = tk.Button(self.root, text="Los", command=self.number_action)
        number_action_button.grid(row=6, column=2, pady=10)

        ### ROW 7
        # Divider line
        divider = ttk.Separator(self.root, orient='horizontal')
        divider.grid(row=7, column=0, columnspan=5, sticky='ew', pady=10)

        ### ROW 8
        # Headline
        headline_label = tk.Label(self.root, text="Unendlich drehen", font=("Helvetica", 10))
        headline_label.grid(row=8, column=0, columnspan=5, pady=10, sticky='w')


        ### ROW 9
        # Checkbox for clockwise rotation
        clockwise_label = tk.Label(self.root, text="Clockwise:")
        clockwise_label.grid(row=9, column=0, pady=10)
        clockwise_checkbox = tk.Checkbutton(self.root, variable=self.clockwise_var, command=self.flip_direction)
        clockwise_checkbox.grid(row=9, column=1, pady=10)
        # Button below 'Close Port'
        custom_button = tk.Button(self.root, text="Starten", command=self.send_start)
        custom_button.grid(row=9, column=2, pady=10)

        # Send 'stop' button
        send_button = tk.Button(self.root, text="Stoppen", command=self.send_stop)
        send_button.grid(row=9, column=3, pady=10)
                
        ### ROW 11
        # Divider line
        divider = ttk.Separator(self.root, orient='horizontal')
        divider.grid(row=11, column=0, columnspan=5, sticky='ew', pady=10)

        ### ROW 12
        # Headline
        headline_label = tk.Label(self.root, text="Globale Einstellungen", font=("Helvetica", 10))
        headline_label.grid(row=12, column=0, columnspan=5, pady=10, sticky='w')

        ### ROW 13
        # Input field for a number
        number_label_speed = tk.Label(self.root, text="Geschwindigkeit:")
        number_label_speed.grid(row=13, column=0, pady=10)

        self.number_entry_speed = tk.Entry(self.root)
        self.number_entry_speed.grid(row=13, column=1, pady=10)

        # Button for triggering an action related to the entered number
        number_action_button = tk.Button(self.root, text="Ändern", command=self.number_action_speed)
        number_action_button.grid(row=13, column=2, pady=10)

        # Button for saving settings to EEPROM
        burn_action_label = tk.Label(self.root, text="Aktuelle Einstellungen speichern und beim Anstecken automatisch laden: ")
        burn_action_label.grid(row=14, column=0, pady=10)
        burn_action_button = tk.Button(self.root, text="Burn Settings", command=self.send_burn)
        burn_action_button.grid(row=14, column=1, pady=10)
        erase_action_button = tk.Button(self.root, text="Erase Settings", command=self.send_erase)
        erase_action_button.grid(row=14, column=2, pady=10)

        ### ROW 14
        # Text widget for displaying sent and received messages
        self.text_widget = tk.Text(self.root, height=10, width=80)  # Adjust width here
        self.text_widget.grid(row=15, column=0, pady=10, columnspan=5)


    def get_serial_ports(self):
        """Return a list of available serial ports."""
        ports = [port.device for port in comports()]
        return ports

    def get_material_design_icon(self, url, size):
        """Download Material Design icon and create an Image object."""
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses
            icon_data = BytesIO(response.content)
            icon_image = Image.open(icon_data).resize(size, Image.ANTIALIAS)
            return ImageTk.PhotoImage(icon_image)
        except requests.RequestException as e:
            print(f"Error downloading icon: {e}")
            return None
        except Exception as e:
            print(f"Error creating ImageTk: {e}")
            return None

    def refresh_ports(self):
        """Refresh the list of available serial ports."""
        self.serial_ports = self.get_serial_ports()
        self.serial_port_var.set("Select Port")
        self.insert_message("Refreshed serial ports.", "dark blue")

    def send_stop(self):
        self.send_command(commands["stop"])
    
    def send_start(self):
        self.send_command(commands["start"])
    
    def send_steps(self, steps):
        self.send_command(commands["steps"] + str(steps).encode())
    
    def send_clockwise(self):
        self.send_command(commands["clockwise"])
    def send_counter_clockwise(self):
        self.send_command(commands["counterclockwise"])
    
    def send_speed(self, speed):
        self.send_command(commands["speed"] + str(speed).encode())

    def send_burn(self):
        self.send_command(commands["burn"])

    def send_erase(self):
        self.send_command(commands["erase"])


    def send_command(self, command):
        """Send 'stop' to the selected serial port."""
        self.selected_port = self.serial_port_var.get()

        if self.selected_port == "Select Port":
            self.insert_message("Please select a valid serial port.", "dark blue")
            return

        try:
            if self.serial and self.serial.is_open:
                self.serial.write(command)
                self.insert_message(f"Sent {command} command to Arduino on {self.selected_port}", "dark blue")
            else:
                self.insert_message("Serial port is not open.", "dark blue")
        except Exception as e:
            self.insert_message(f"Error: {e}", "dark blue")

    def toggle_serial_port(self):
        """Open or close the selected serial port."""
        if not self.serial or not self.serial.is_open:
            self.open_serial_port()
        else:
            self.close_serial_port()

    def open_serial_port(self):
        """Open the selected serial port."""
        self.selected_port = self.serial_port_var.get()

        if self.selected_port == "Select Port":
            self.insert_message("Please select a valid serial port.", "dark blue")
            return

        try:
            self.serial = serial.Serial(self.selected_port, 115200, timeout=1)
            self.open_close_button.config(text="Close Port")
            self.insert_message(f"Opened serial port on {self.selected_port}", "dark blue")
        except Exception as e:
            self.insert_message(f"Error opening serial port: {e}", "dark blue")

    def close_serial_port(self):
        """Close the open serial port."""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                self.open_close_button.config(text="Open Port")
                self.insert_message("Closed serial port.", "dark blue")
            else:
                self.insert_message("Serial port is not open.", "dark blue")
        except Exception as e:
            self.insert_message(f"Error closing serial port: {e}", "dark blue")

    def flip_direction(self):
        """Perform a custom action based on the checkbox and input field."""
        is_clockwise = self.clockwise_var.get()

        action_message = f"Custom Action: {'Clockwise' if is_clockwise else 'Counter-Clockwise'}"
        self.insert_message(action_message, "dark blue")
        if is_clockwise:
            self.send_clockwise()
            self.clockwise_var.set(True)
        else:
            self.send_counter_clockwise()

    def number_action(self):
        """Perform an action related to the entered number."""
        number_value = self.get_number_entry_value()
        action_message = f"Tilt Modus, Schwenke {number_value} Schritte vor und zurück"
        self.insert_message(action_message, "dark blue")
        self.send_steps(number_value)
    
    def number_action_speed(self):
        """Perform an action related to the entered number."""
        number_value = self.get_speed_entry_value()
        action_message = f"Ändere Geschwindigkeit zu {number_value} "
        self.insert_message(action_message, "dark blue")
        self.send_speed(number_value)

    def read_serial(self):
        """Read from the serial port and update the text widget."""
        try:
            if self.serial and self.serial.is_open:
                received_data = self.serial.readline().decode('utf-8').strip()
                if received_data:
                    self.insert_message(f"Received: {received_data}", "dark green")
        except Exception as e:
            self.insert_message(f"Error reading from serial port: {e}", "dark blue")

        # Schedule the read_serial function to be called again after 1000 milliseconds (1 second)
        self.root.after(10, self.read_serial)

    def setup_serial(self):
        """Set up the initial serial port reading."""
        self.root.after(10, self.read_serial)

    def insert_message(self, message, color):
        """Insert a message into the text widget with the specified color."""
        self.text_widget.tag_config(color, foreground=color)
        self.text_widget.insert(tk.END, message + "\n", color)
        self.text_widget.see(tk.END)

    def get_number_entry_value(self):
        """Get the value from the number entry field."""
        try:
            return int(self.number_entry.get())
        except ValueError:
            self.insert_message("Invalid number. Please enter a valid number.", "dark blue")
            return 0
    
    def get_speed_entry_value(self):
        """Get the value from the speed entry field."""
        try:
            return int(self.number_entry_speed.get())
        except ValueError:
            self.insert_message("Invalid number. Please enter a valid speed.", "dark blue")
            return 0


if __name__ == "__main__":
    root = tk.Tk()
    app = ArduinoControlApp(root)
    root.mainloop()
