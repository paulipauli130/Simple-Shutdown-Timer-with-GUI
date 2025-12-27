import tkinter as tk
import subprocess
import threading
import time
from datetime import timedelta
import os
import sys

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

shutdown_end_time = None
tray_icon = None

# Funktion für Tray-Icon
def create_image():
    img = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(img)
    d.rectangle((16, 16, 48, 48), fill="white")
    return img

def format_remaining():
    if shutdown_end_time is None:
        return "Kein Timer aktiv"
    remaining = int(shutdown_end_time - time.time())
    if remaining < 0:
        return "0s"
    return str(timedelta(seconds=remaining))

def update_countdown():
    while True:
        if shutdown_end_time:
            label_status.config(text=f"Verbleibend: {format_remaining()}")
        time.sleep(1)

def start_shutdown_seconds(seconds):
    global shutdown_end_time
    shutdown_end_time = time.time() + seconds
    subprocess.run(["shutdown", "/s", "/t", str(seconds)])
    if not always_on_top.get():
        minimize_to_tray()

def start_custom():
    h = int(entry_hours.get() or 0)
    m = int(entry_minutes.get() or 0)
    seconds = h * 3600 + m * 60
    if seconds <= 0:
        label_status.config(text="Zeit > 0 eingeben")
        return
    start_shutdown_seconds(seconds)

def abort_shutdown(icon=None, item=None):
    global shutdown_end_time
    shutdown_end_time = None
    subprocess.run(["shutdown", "/a"])
    label_status.config(text="Shutdown abgebrochen")

def minimize_to_tray():
    root.withdraw()
    show_tray()

def show_window(icon=None, item=None):
    root.after(0, root.deiconify)

def quit_app(icon=None, item=None):
    abort_shutdown()
    if tray_icon:
        tray_icon.stop()
    root.destroy()

def show_tray():
    global tray_icon
    if tray_icon:
        return

    def tooltip():
        return f"P's Shutdown Timer – {format_remaining()}"

    tray_icon = pystray.Icon(
        "shutdown_timer",
        create_image(),
        "P's Shutdown Timer",
        menu=pystray.Menu(
            item("Öffnen", show_window, default=True),
            item("Shutdown abbrechen", abort_shutdown),
            item("Beenden", quit_app),
        )
    )

    def updater():
        while True:
            tray_icon.title = tooltip()
            time.sleep(1)

    threading.Thread(target=updater, daemon=True).start()
    threading.Thread(target=tray_icon.run, daemon=True).start()

# GUI
root = tk.Tk()
root.title("P's Shutdown Timer")
root.resizable(False, False)

# Fenster-Icon absolut laden (funktioniert auch in EXE)
if getattr(sys, 'frozen', False):
    # Script als EXE
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(base_path, "icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

always_on_top = tk.BooleanVar()
tk.Checkbutton(root, text="Fenster immer im Vordergrund",
               variable=always_on_top,
               command=lambda: root.attributes("-topmost", always_on_top.get())
               ).grid(row=0, column=0, columnspan=4, pady=5)

tk.Label(root, text="Stunden").grid(row=1, column=0)
tk.Label(root, text="Minuten").grid(row=1, column=2)

entry_hours = tk.Entry(root, width=5)
entry_minutes = tk.Entry(root, width=5)
entry_hours.grid(row=1, column=1)
entry_minutes.grid(row=1, column=3)

tk.Button(root, text="Start", command=start_custom).grid(row=2, column=0, columnspan=4, pady=5)

# Presets
presets = [
    ("1 min", 60), ("5 min", 300), ("10 min", 600), ("15 min", 900), ("30 min", 1800),
    ("1h", 3600), ("1h30", 5400), ("2h", 7200), ("3h", 10800),
    ("4h", 14400), ("5h", 18000),
]

row = 3
col = 0
for text, sec in presets:
    tk.Button(root, text=text, width=8,
              command=lambda s=sec: start_shutdown_seconds(s)
              ).grid(row=row, column=col, padx=2, pady=2)
    col += 1
    if col > 3:
        col = 0
        row += 1

tk.Button(root, text="Abbrechen", command=abort_shutdown).grid(row=row+1, column=0, columnspan=4, pady=5)

label_status = tk.Label(root, text="Kein Timer aktiv")
label_status.grid(row=row+2, column=0, columnspan=4, pady=5)

# Countdown-Thread starten
threading.Thread(target=update_countdown, daemon=True).start()

root.mainloop()
