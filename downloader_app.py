import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import os
import threading
import pyperclip
from pathlib import Path
import sys
import logging

# === Folder Setup ===
MUSIC_DIR = str(Path.home() / "Music")
BASE_OUTPUT_DIR = os.path.join(MUSIC_DIR, "Unsorted Music")
ERROR_LOG = os.path.join(MUSIC_DIR, "SpotDL_Errors.txt")
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

# === Logging Setup ===
logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)], level=logging.INFO, encoding="utf-8")

# === Match Mode Descriptions ===
MATCH_MODE_EXPLAIN = {
    "Default (Best)": "Standard/Best Match: SpotDL will auto-select the best available match for your song. This is recommended for most users.",
    "Verified (Strict)": "Strict Verified: Only downloads tracks with a perfect match (may skip obscure/remixes). Use for high accuracy.",
    "Fuzzy (Lenient)": "Lenient/Fuzzy: Downloads anything that looks close, even if it's not a perfect match (good for remixes, rare, or covers)."
}

class DJDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 DJDownloader")
        self.root.geometry("820x600")
        self.root.resizable(False, False)

        self.output_dir = BASE_OUTPUT_DIR
        self.queue = []

        self.theme = "dark"
        self.match_mode = tk.StringVar(value="Default (Best)")
        self.force_mode = tk.BooleanVar(value=True)

        self.setup_style()
        self.setup_widgets()
        self.log("✅ DJDownloader Ready.")

    def setup_style(self):
        self.bg_dark = "#1e1e1e"
        self.fg_dark = "#ffffff"
        self.bg_light = "#f2f2f2"
        self.fg_light = "#000000"
        self.update_theme(self.theme)

    def update_theme(self, theme):
        bg = self.bg_dark if theme == "dark" else self.bg_light
        fg = self.fg_dark if theme == "dark" else self.fg_light
        self.root.configure(bg=bg)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TButton", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TLabel", background=bg, foreground=fg)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.update_theme(self.theme)

    def setup_widgets(self):
        ttk.Button(self.root, text="🌗 Toggle Theme", command=self.toggle_theme).pack(pady=5)

        self.link_entry = tk.Entry(self.root, width=90, font=("Segoe UI", 10))
        self.link_entry.pack(pady=10)

        ttk.Button(self.root, text="📋 Paste from Clipboard", command=self.paste_clipboard).pack()

        action_frame = tk.Frame(self.root, bg=self.root["bg"])
        action_frame.pack(pady=5)
        ttk.Button(action_frame, text="⬇️ Add to Queue", command=self.queue_link).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="📂 Load .txt", command=self.load_txt).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="🚀 Start Download", command=self.start_download).grid(row=0, column=2, padx=5)

        ttk.Button(self.root, text="📁 Choose Folder", command=self.choose_output_directory).pack(pady=5)

        # --- Match Mode Dropdown with Tooltip ---
        match_mode_frame = tk.Frame(self.root, bg=self.root["bg"])
        match_mode_frame.pack(pady=5)
        tk.Label(match_mode_frame, text="Match Mode:", bg=self.root["bg"], fg=self.fg_dark).pack(side="left")

        match_mode_dropdown = ttk.Combobox(
            match_mode_frame, textvariable=self.match_mode, width=24, state="readonly",
            values=list(MATCH_MODE_EXPLAIN.keys())
        )
        match_mode_dropdown.pack(side="left", padx=4)

        # Tooltip
        tooltip = tk.Label(
            match_mode_frame, text="?", fg="#1e90ff", bg=self.root["bg"], font=("Segoe UI", 14, "bold"),
            cursor="question_arrow"
        )
        tooltip.pack(side="left")
        def on_enter(_):
            selected = self.match_mode.get()
            expl = MATCH_MODE_EXPLAIN.get(selected, "")
            tooltip_tip = tk.Toplevel(self.root)
            tooltip_tip.wm_overrideredirect(True)
            x, y = self.root.winfo_pointerxy()
            tooltip_tip.wm_geometry(f"+{x+18}+{y-22}")
            msg = tk.Label(tooltip_tip, text=expl, bg="#262C34", fg="#cce7ff", font=("Segoe UI", 9), relief="solid", borderwidth=1, padx=8, pady=6, wraplength=340, justify="left")
            msg.pack()
            tooltip.tooltip_window = tooltip_tip
        def on_leave(_):
            if hasattr(tooltip, "tooltip_window") and tooltip.tooltip_window:
                tooltip.tooltip_window.destroy()
                tooltip.tooltip_window = None
        tooltip.bind("<Enter>", on_enter)
        tooltip.bind("<Leave>", on_leave)

        options_frame = tk.Frame(self.root, bg=self.root["bg"])
        options_frame.pack(pady=5)
        ttk.Checkbutton(options_frame, text="🔁 Force Overwrite", variable=self.force_mode).pack(side="left", padx=10)

        self.queue_display = scrolledtext.ScrolledText(self.root, width=100, height=8, font=("Consolas", 9))
        self.queue_display.pack(pady=10)
        self.queue_display.insert(tk.END, "📝 Queue will appear here...\n")
        self.queue_display.configure(state="disabled")

        self.log_output = scrolledtext.ScrolledText(self.root, width=100, height=12, font=("Consolas", 9))
        self.log_output.pack()

        ttk.Button(self.root, text="📂 Open Output Folder", command=self.open_output_folder).pack(pady=5)

    def log(self, text):
        clean_text = text.encode("ascii", "ignore").decode(errors="ignore")
        self.log_output.configure(state="normal")
        self.log_output.insert(tk.END, f"{clean_text}\n")
        self.log_output.configure(state="disabled")
        self.log_output.see(tk.END)

    def update_queue_display(self):
        self.queue_display.configure(state="normal")
        self.queue_display.delete(1.0, tk.END)
        for i, item in enumerate(self.queue, 1):
            self.queue_display.insert(tk.END, f"{i}. {item}\n")
        self.queue_display.configure(state="disabled")

    def paste_clipboard(self):
        try:
            data = pyperclip.paste()
            self.link_entry.delete(0, tk.END)
            self.link_entry.insert(0, data)
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))

    def queue_link(self):
        link = self.link_entry.get().strip()
        if link:
            self.queue.append(link)
            self.update_queue_display()
            self.link_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Missing Link", "Paste a Spotify or YouTube link first.")

    def load_txt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    link = line.strip()
                    if link:
                        self.queue.append(link)
            self.update_queue_display()

    def choose_output_directory(self):
        selected_dir = filedialog.askdirectory(title="Select Download Folder")
        if selected_dir:
            self.output_dir = selected_dir
            os.makedirs(self.output_dir, exist_ok=True)
            messagebox.showinfo("Download Folder Updated", self.output_dir)

    def open_output_folder(self):
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)

    def start_download(self):
        if not self.queue:
            messagebox.showwarning("Queue Empty", "Add something to the queue first.")
            return
        threading.Thread(target=self.download_queue, daemon=True).start()

    def download_queue(self):
        while self.queue:
            target = self.queue.pop(0)
            self.update_queue_display()
            self.log(f"🎧 Downloading: {target}")

            try:
                is_spotify = "open.spotify.com" in target
                is_youtube = any(domain in target for domain in [
                    "youtube.com/", "youtu.be/", "music.youtube.com/"
                ])

                if is_spotify:
                    # Save in Spotify folder
                    output_folder = os.path.join(self.output_dir, "Spotify")
                    os.makedirs(output_folder, exist_ok=True)
                    output_path = os.path.join(output_folder, "{title} - {artist}.{output_ext}")

                    cmd = [
                        "spotdl", "download", target,
                        "--output", output_path,
                        "--save-errors", ERROR_LOG,
                        "--print-errors"
                    ]

                    # Add match mode
                    mode = self.match_mode.get()
                    if "Verified" in mode:
                        cmd.append("--only-verified-results")
                    elif "Fuzzy" in mode:
                        cmd.append("--dont-filter-results")
                    # Overwrite mode
                    if self.force_mode.get():
                        cmd += ["--overwrite", "force"]

                elif is_youtube:
                    # Save in YouTube folder
                    output_folder = os.path.join(self.output_dir, "YouTube")
                    os.makedirs(output_folder, exist_ok=True)
                    output_path = os.path.join(output_folder, "%(title)s.%(ext)s")
                    cmd = [
                        "yt-dlp", "-f", "bestaudio/best",
                        "--extract-audio", "--audio-format", "mp3",
                        "-o", output_path,
                        target
                    ]
                else:
                    self.log(f"❌ Unsupported link type: {target}")
                    continue

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                for line in process.stdout:
                    self.log(line.strip())
                    # SpotDL error tip
                    if "Failed to convert" in line and is_spotify:
                        self.log("💡 SpotDL failed: Try using the YouTube link for this song directly if audio not found!")

                process.wait()
                self.log(f"✅ Done: {target}")

            except Exception as e:
                self.log(f"❌ Error: {e}")

        messagebox.showinfo("Done", "✅ All downloads finished.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DJDownloaderApp(root)
    root.mainloop()
