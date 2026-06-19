import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button

# Initialisierung der Controller
keyboard = KeyboardController()
mouse = MouseController()

class AutoActionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Clicker & -Presser")
        self.root.geometry("380x420")
        self.root.resizable(False, False)

        self.running = False
        self.action_thread = None

        # Style
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        # --- GUI Elemente ---
        
        # Frame für die Eingabefelder
        input_frame = ttk.LabelFrame(self.root, text="Aktionen konfigurieren", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # --- Tastendruck-spezifische Eingaben ---
        self.key_action_enabled = tk.BooleanVar(value=True)
        self.key_checkbox = ttk.Checkbutton(input_frame, text="Tastedrücke aktiv", variable=self.key_action_enabled, command=self.toggle_ui_elements)
        self.key_checkbox.grid(row=0, column=0, columnspan=2, padx=5, pady=(5,0), sticky=tk.W)

        # Tasten-Eingabefelder (bis zu 4 Tasten)
        self.key_entries = []
        for i in range(4):
            label_text = f"   Taste {i+1}:"
            ttk.Label(input_frame, text=label_text).grid(row=1+i, column=0, padx=5, pady=2, sticky=tk.W)
            key_entry = ttk.Entry(input_frame, width=25)
            key_entry.grid(row=1+i, column=1, padx=5, pady=2)
            self.key_entries.append(key_entry)
        
        # Standard-Tasten setzen
        self.key_entries[0].insert(0, "a")
        
        # Separator
        ttk.Separator(input_frame, orient='horizontal').grid(row=5, columnspan=2, sticky='ew', pady=10)

        # --- Mausklick-spezifische Eingaben ---
        self.mouse_action_enabled = tk.BooleanVar(value=False)
        self.mouse_checkbox = ttk.Checkbutton(input_frame, text="Mausklick aktiv", variable=self.mouse_action_enabled, command=self.toggle_ui_elements)
        self.mouse_checkbox.grid(row=6, column=0, columnspan=2, padx=5, pady=(5,0), sticky=tk.W)

        ttk.Label(input_frame, text="   Maustaste:").grid(row=7, column=0, padx=5, pady=2, sticky=tk.W)
        self.mouse_button_var = tk.StringVar(value="Links")
        self.mouse_button_combo = ttk.Combobox(input_frame, textvariable=self.mouse_button_var, width=22, state="readonly")
        self.mouse_button_combo['values'] = ('Links', 'Rechts', 'Mittel')
        self.mouse_button_combo.grid(row=7, column=1, padx=5, pady=2)
        
        # --- Gemeinsame Eingaben ---
        ttk.Label(input_frame, text="Intervall (ms):").grid(row=8, column=0, padx=5, pady=(15, 5), sticky=tk.W)
        self.interval_entry = ttk.Entry(input_frame, width=25)
        self.interval_entry.grid(row=8, column=1, padx=5, pady=(15, 5))
        self.interval_entry.insert(0, "500")

        # --- Steuerung ---
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_actions)
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_actions, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        self.status_label = ttk.Label(self.root, text="Status: Gestoppt", padding="10")
        self.status_label.pack(fill=tk.X)
        
        self.toggle_ui_elements()

    def toggle_ui_elements(self):
        """Aktiviert/Deaktiviert Eingabefelder basierend auf der Checkbox-Auswahl."""
        for key_entry in self.key_entries:
            key_entry.config(state=tk.NORMAL if self.key_action_enabled.get() else tk.DISABLED)
        self.mouse_button_combo.config(state='readonly' if self.mouse_action_enabled.get() else tk.DISABLED)

    def action_loop(self):
        """Die Schleife, die die ausgewählten Aktionen wiederholt ausführt."""
        try:
            interval_ms = self.interval_entry.get()
            interval_sec = int(interval_ms) / 1000.0
            if interval_sec <= 0:
                raise ValueError("Intervall muss positiv sein.")

            # Prüfen, welche Aktionen ausgeführt werden sollen
            key_enabled = self.key_action_enabled.get()
            mouse_enabled = self.mouse_action_enabled.get()
            
            # Tasten sammeln (nur nicht-leere Einträge)
            keys_to_press = []
            if key_enabled:
                for key_entry in self.key_entries:
                    key_text = key_entry.get().strip()
                    if key_text:
                        keys_to_press.append(key_text)
                
                if not keys_to_press:
                    messagebox.showerror("Fehler", "Bitte geben Sie mindestens eine Taste an.")
                    self.stop_actions()
                    return

            button_map = {'Links': Button.left, 'Rechts': Button.right, 'Mittel': Button.middle}
            button_to_click = button_map.get(self.mouse_button_var.get()) if mouse_enabled else None

            # Die eigentliche Aktionsschleife
            while self.running:
                if key_enabled:
                    # Alle Tasten nacheinander drücken und freigeben
                    for key in keys_to_press:
                        keyboard.press(key)
                    
                    # Kurze Verzögerung zwischen Drücken und Freigeben
                    time.sleep(0.05)
                    
                    for key in keys_to_press:
                        keyboard.release(key)
                
                if mouse_enabled:
                    mouse.click(button_to_click, 1)
                
                time.sleep(interval_sec)

        except ValueError:
            messagebox.showerror("Fehler", "Ungültiges Intervall. Bitte geben Sie eine positive Zahl ein.")
            self.stop_actions()
        except Exception as e:
            messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten:\n{e}")
            self.stop_actions()

    def start_actions(self):
        """Startet den Aktions-Prozess."""
        if self.running:
            return
            
        if not self.key_action_enabled.get() and not self.mouse_action_enabled.get():
            messagebox.showinfo("Info", "Bitte aktivieren Sie mindestens eine Aktion (Tastendruck oder Mausklick).")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Läuft...")

        # Alle Eingabeelemente deaktivieren
        self.key_checkbox.config(state=tk.DISABLED)
        self.mouse_checkbox.config(state=tk.DISABLED)
        for key_entry in self.key_entries:
            key_entry.config(state=tk.DISABLED)
        self.mouse_button_combo.config(state=tk.DISABLED)
        self.interval_entry.config(state=tk.DISABLED)

        self.action_thread = threading.Thread(target=self.action_loop, daemon=True)
        self.action_thread.start()

    def stop_actions(self):
        """Stoppt den Aktions-Prozess."""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Gestoppt")
        
        # Eingabeelemente wieder aktivieren
        self.key_checkbox.config(state=tk.NORMAL)
        self.mouse_checkbox.config(state=tk.NORMAL)
        self.interval_entry.config(state=tk.NORMAL)
        self.toggle_ui_elements() # UI-Status entsprechend der Checkboxen wiederherstellen

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoActionApp(root)
    root.mainloop()
