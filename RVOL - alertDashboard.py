import tkinter as tk
from tkinter import ttk
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import queue
import numpy as np
import time

class RVOLScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Intraday RVOL Scanner")
        self.gui_queue = queue.Queue()

        # --- State Management Variables ---
        self.live_scan_thread = None
        self.is_live_scanning = False
        self.is_paused = False

        # --- GUI Elements ---
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Controls Frame ---
        controls_frame = ttk.LabelFrame(self.main_frame, text="Scan Controls", padding="10")
        controls_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # RVOL Threshold
        rvol_label = ttk.Label(controls_frame, text="RVOL Threshold:")
        rvol_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.rvol_entry = ttk.Entry(controls_frame, width=10)
        self.rvol_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.rvol_entry.insert(0, "2.0")

        # Timeframe Selection
        timeframe_label = ttk.Label(controls_frame, text="Timeframe:")
        timeframe_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.timeframe_var = tk.StringVar()
        self.timeframe_combobox = ttk.Combobox(controls_frame, textvariable=self.timeframe_var, state="readonly", width=8)
        self.timeframe_combobox['values'] = ('1m', '2m', '5m', '15m', '30m', '60m', '90m')
        self.timeframe_combobox.set('5m')
        self.timeframe_combobox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # --- Test Mode Section ---
        self.test_mode_frame = ttk.LabelFrame(self.main_frame, text="Test Mode", padding="10")
        self.test_mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.date_label = ttk.Label(self.test_mode_frame, text="Date (YYYY-MM-DD):")
        self.date_label.grid(row=0, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(self.test_mode_frame)
        self.date_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.date_entry.insert(0, "2023-11-15")

        self.time_label = ttk.Label(self.test_mode_frame, text="Time (HH:MM EST):")
        self.time_label.grid(row=1, column=0, sticky=tk.W)
        self.time_entry = ttk.Entry(self.test_mode_frame)
        self.time_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        self.time_entry.insert(0, "10:30")

        self.run_test_button = ttk.Button(self.test_mode_frame, text="Run Test Scan", command=self.start_test_scan)
        self.run_test_button.grid(row=2, column=0, columnspan=2, pady=5)

        # --- Live Scan Buttons ---
        live_buttons_frame = ttk.Frame(self.main_frame)
        live_buttons_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        self.start_stop_button = ttk.Button(live_buttons_frame, text="Start Live Scan", command=self.toggle_live_scan)
        self.start_stop_button.grid(row=0, column=0, padx=5)
        self.pause_resume_button = ttk.Button(live_buttons_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_resume_button.grid(row=0, column=1, padx=5)


        # --- Results and Debug Paned Window ---
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.paned_window.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.results_frame = ttk.LabelFrame(self.paned_window, text="High RVOL Tickers", padding="10")
        self.paned_window.add(self.results_frame, weight=2)
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD, height=10)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.debug_frame = ttk.LabelFrame(self.paned_window, text="Debug Log", padding="10")
        self.paned_window.add(self.debug_frame, weight=1)
        self.debug_text = tk.Text(self.debug_frame, wrap=tk.WORD, height=8, fg="gray")
        self.debug_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # --- NEW: Progress Bar ---
        self.progress_bar = ttk.Progressbar(self.main_frame, orient='horizontal', mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        self.status_label = ttk.Label(self.main_frame, text="Status: Idle")
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))

        self.configure_resizing()
        self.root.after(100, self.process_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_resizing(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(3, weight=1) # The paned window is the resizable one
        self.results_frame.columnconfigure(0, weight=1)
        self.results_frame.rowconfigure(0, weight=1)
        self.debug_frame.columnconfigure(0, weight=1)
        self.debug_frame.rowconfigure(0, weight=1)

    # --- Thread-safe GUI update methods ---
    def log_debug(self, message):
        self.gui_queue.put(("debug", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n"))

    def update_results(self, result, clear_first=False):
        self.gui_queue.put(("result", (result, clear_first)))

    def update_status(self, message):
        self.gui_queue.put(("status", f"Status: {message}"))
    
    # --- NEW: Thread-safe progress bar update ---
    def update_progress(self, value, max_value):
        self.gui_queue.put(("progress", (value, max_value)))

    def process_queue(self):
        try:
            while not self.gui_queue.empty():
                msg_type, data = self.gui_queue.get_nowait()
                if msg_type == "debug":
                    self.debug_text.insert(tk.END, data)
                    self.debug_text.see(tk.END)
                elif msg_type == "result":
                    result, clear_first = data
                    if clear_first:
                        self.results_text.delete("1.0", tk.END)
                    self.results_text.insert(tk.END, result)
                elif msg_type == "status":
                    self.status_label.config(text=data)
                # --- NEW: Handle progress bar messages ---
                elif msg_type == "progress":
                    value, max_value = data
                    if max_value > 0:
                        self.progress_bar['maximum'] = max_value
                        self.progress_bar['value'] = value
                    else: # Reset/hide the bar
                        self.progress_bar['value'] = 0

        finally:
            self.root.after(100, self.process_queue)

    # --- Button Command Methods (Unchanged) ---
    def start_test_scan(self):
        date_str = self.date_entry.get()
        time_str = self.time_entry.get()
        if date_str and time_str:
            try:
                test_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                self.start_scan_thread(test_mode=True, test_datetime=test_datetime)
            except ValueError:
                self.update_status("Error: Invalid date/time format.")
        else:
            self.update_status("Error: Please enter date and time for test mode.")

    def toggle_live_scan(self):
        if self.is_live_scanning:
            self.is_live_scanning = False
            self.start_stop_button.config(text="Start Live Scan")
            self.pause_resume_button.config(state="disabled", text="Pause")
            self.log_debug("Stop signal sent to live scanner.")
        else:
            self.is_live_scanning = True
            self.is_paused = False
            self.start_stop_button.config(text="Stop Live Scan")
            self.pause_resume_button.config(state="normal", text="Pause")
            self.start_scan_thread(test_mode=False)

    def toggle_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.pause_resume_button.config(text="Pause")
            self.update_status("Live Scan Resumed.")
        else:
            self.is_paused = True
            self.pause_resume_button.config(text="Resume")
            self.update_status("Live Scan Paused.")

    def on_closing(self):
        self.is_live_scanning = False
        self.root.destroy()

    # --- Scanning Logic ---
    def start_scan_thread(self, test_mode, test_datetime=None):
        self.debug_text.delete("1.0", tk.END)
        self.update_status("Starting scan...")
        self.live_scan_thread = threading.Thread(target=self.run_scan_loop, args=(test_mode, test_datetime))
        self.live_scan_thread.daemon = True
        self.live_scan_thread.start()

    def run_scan_loop(self, test_mode, test_datetime):
        try:
            rvol_threshold = float(self.rvol_entry.get())
        except ValueError:
            self.log_debug("Invalid RVOL threshold. Defaulting to 2.0.")
            rvol_threshold = 2.0

        interval = self.timeframe_var.get()
        timeframe_seconds = {'1m': 60, '2m': 120, '5m': 300, '15m': 900, '30m': 1800, '60m': 3600, '90m': 5400}
        wait_seconds = timeframe_seconds.get(interval, 300)

        try:
            # IMPORTANT: Update this path to your ticker file
            ticker_file_path = 'D:/Python/Russell3000Holdings.csv'
            self.log_debug(f"Reading tickers from: {ticker_file_path}")
            with open(ticker_file_path, 'r') as f:
                tickers = [line.strip() for line in f if line.strip()]
            self.log_debug(f"Loaded {len(tickers)} tickers.")
        except FileNotFoundError:
            self.log_debug(f"FATAL ERROR: The file '{ticker_file_path}' was not found.")
            self.update_status(f"Error: tickers.csv not found.")
            return

        scan_loop_active = True
        while scan_loop_active and (self.is_live_scanning or test_mode):
            if not self.is_paused:
                self.update_results("", clear_first=True)
                # Pass the ticker list to the scanning logic
                self._perform_scan_logic(tickers, rvol_threshold, interval, test_mode, test_datetime)

                if test_mode:
                    self.update_status("Test scan complete.")
                    scan_loop_active = False # End loop after one run in test mode
                else:
                    self.update_status(f"Scan complete. Waiting for next {interval} candle...")
                    # Responsive wait loop
                    for _ in range(wait_seconds):
                        if not self.is_live_scanning: break
                        time.sleep(1)
            else:
                time.sleep(1) # Sleep briefly while paused

        if not test_mode:
            self.update_status("Live scan stopped.")
        self.update_progress(0, 0) # Final reset of the progress bar

    def _perform_scan_logic(self, tickers, rvol_threshold, interval, test_mode, test_datetime):
        num_tickers = len(tickers)
        self.update_progress(0, num_tickers) # Initialize progress bar

        lookback_days = 20
        # --- MODIFIED: Use enumerate to get index for progress bar ---
        for i, ticker in enumerate(tickers):
            if not self.is_live_scanning and not test_mode: break
            while self.is_paused: time.sleep(1)

            self.update_status(f"Scanning: {ticker} ({i+1}/{num_tickers})")
            try:
                # (The rest of the yfinance logic is unchanged)
                end_date = test_datetime if test_mode else datetime.now() + timedelta(days=1)
                start_date = end_date - timedelta(days=lookback_days)

                hist_data = yf.download(ticker, start=start_date, end=end_date, interval=interval, auto_adjust=True, progress=False)

                if hist_data.empty:
                    self.log_debug(f"[{ticker}] No data returned from yfinance.")
                    continue

                if test_mode:
                    market_tz = hist_data.index.tz
                    target_time = pd.Timestamp(test_datetime, tz=market_tz)
                    latest_candle = hist_data.loc[hist_data.index == target_time]
                else:
                    latest_candle = hist_data.iloc[-1:]

                if latest_candle.empty:
                    self.log_debug(f"[{ticker}] Could not find a candle for the target time.")
                    continue

                latest_volume = float(latest_candle['Volume'].iloc[0])
                latest_time = latest_candle.index[0].time()

                same_time_candles = hist_data[hist_data.index.time == latest_time]
                average_volume = float(same_time_candles['Volume'].mean())

                if np.isnan(average_volume):
                    self.log_debug(f"[{ticker}] Could not calculate average volume (NaN result).")
                    continue

                if average_volume > 0:
                    rvol = latest_volume / average_volume
                    if rvol >= rvol_threshold:
                        result = f"{ticker}: RVOL = {rvol:.2f} (Vol: {latest_volume:.0f}, Avg Vol: {average_volume:.0f})\n"
                        self.log_debug(f"[{ticker}] MEETS CRITERIA! RVOL is {rvol:.2f}")
                        self.update_results(result)
            except Exception as e:
                self.log_debug(f"[{ticker}] AN ERROR OCCURRED: {e}")
            finally:
                # --- MODIFIED: Update progress bar after each ticker ---
                self.update_progress(i + 1, num_tickers)

if __name__ == "__main__":
    root = tk.Tk()
    app = RVOLScanner(root)
    root.mainloop()