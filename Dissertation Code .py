import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import use
use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
import threading  # For asynchronous processing

class BreathAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real-Time Breath Acetone Analysis")
        self.geometry("900x700")
        self.configure(bg="#f0f0f0")
        
        self.is_running = False
        self.is_paused = False
        self.data = pd.DataFrame(columns=['time', 'acetone', 'error', 'co2'])
        self.start_time = None
        self.paused_time = 0
        self.update_interval = 10  # Progress bar and timer update interval in milliseconds (0.01 seconds)
        self.data_update_interval = 1000  # Data update interval in milliseconds (1 second)
        self.test_duration = 60  # 60 seconds
        self.remaining_time = self.test_duration

        self.breathing = False
        self.breath_start_time = None
        self.no_breath_detected = 0  # Counter for no breath detected

        self.create_widgets()

    def create_widgets(self):
        # Header label
        header = tk.Label(self, text="Real-Time Breath Acetone Analysis Tool", font=("Arial", 20), bg="#f0f0f0")
        header.pack(pady=20)

        # Frame for controls
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10)
        
        # Start, Pause, and Stop buttons
        start_button = ttk.Button(control_frame, text="Start", command=self.start_simulation)
        start_button.grid(row=0, column=0, padx=10)
        
        pause_button = ttk.Button(control_frame, text="Pause", command=self.pause_simulation)
        pause_button.grid(row=0, column=1, padx=10)
        
        stop_button = ttk.Button(control_frame, text="Stop (Reset)", command=self.stop_simulation)
        stop_button.grid(row=0, column=2, padx=10)
        
        # Progress bar for test duration
        self.progress_bar = ttk.Progressbar(control_frame, length=300, maximum=self.test_duration*100, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=3, pady=10)

        # Label to display the timer
        self.timer_label = tk.Label(control_frame, text=f"Time Remaining: {self.test_duration:.2f} s", font=("Arial", 12))
        self.timer_label.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Treeview for displaying data summary
        self.tree = ttk.Treeview(control_frame, columns=("Time", "Acetone (ppm)", "Error (ppm)", "CO2 (ppm)"), show='headings')
        self.tree.heading("Time", text="Time (s)")
        self.tree.heading("Acetone (ppm)", text="Acetone (ppm)")
        self.tree.heading("Error (ppm)", text="Error (ppm)")
        self.tree.heading("CO2 (ppm)", text="CO2 (ppm)")
        self.tree.grid(row=3, column=0, columnspan=3, padx=10, pady=10)
        
        # Frame for plots
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(pady=10, fill=tk.BOTH, expand=True)
    
    def start_simulation(self):
        if not self.is_running and self.remaining_time > 0:
            self.is_running = True
            if not self.is_paused:
                self.start_time = time.time()
            else:
                # Adjust the start time if resuming from pause
                self.start_time += time.time() - self.paused_time
                self.is_paused = False
            self.update_timer_and_progress_bar()
            threading.Thread(target=self.update_data).start()   # Update data asynchronously using threads

    def pause_simulation(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.paused_time = time.time()
            self.is_running = False
    
    def stop_simulation(self):
        self.is_running = False
        self.is_paused = False
        self.data = pd.DataFrame(columns=['time', 'acetone', 'error', 'co2'])  # Reset data
        self.tree.delete(*self.tree.get_children())  # Clear the treeview
        self.clear_plot()  # Clear the plot
        self.remaining_time = self.test_duration
        self.progress_bar['value'] = 0  # Reset progress bar
        self.timer_label.config(text=f"Time Remaining: {self.test_duration:.2f} s")  # Reset timer

    def update_timer_and_progress_bar(self):
        if self.is_running:
            # Calculate elapsed time and remaining time
            elapsed_time = time.time() - self.start_time
            self.remaining_time = self.test_duration - elapsed_time

            if self.remaining_time <= 0:
                self.stop_simulation()
                messagebox.showinfo("Test Complete", "The 60-second test has finished.")
                return
            
            # Update the progress bar and timer label
            self.progress_bar['value'] = (self.test_duration - self.remaining_time) * 100
            self.timer_label.config(text=f"Time Remaining: {self.remaining_time:.2f} s")

            # Schedule the next update for the progress bar and timer
            self.after(self.update_interval, self.update_timer_and_progress_bar)

    def update_data(self):
        while self.is_running:
            elapsed_time = time.time() - self.start_time
            new_time = round(elapsed_time, 2)
            
            # Simulate data update
            try:
                new_acetone = self.data.iloc[-1]['acetone'] + np.random.normal(0, 0.01)
                new_error = self.data.iloc[-1]['error'] + np.random.normal(0, 0.005)
                new_co2 = self.data.iloc[-1]['co2'] + np.random.normal(0, 0.005)
            except IndexError:
                # Initialize with starting values
                new_acetone = 0.5
                new_error = 0.1
                new_co2 = 0.4
            
            # Insert check_levels function for acetone concentration monitoring
            self.check_levels()

            # Breathing detection logic
            if not self.breathing and new_acetone > 0.2:  # Simulated threshold for breathing start
                self.breathing = True
                self.breath_start_time = new_time
                self.no_breath_detected = 0
            elif self.breathing and new_acetone <= 0.2:  # Simulated threshold for breathing end
                self.breathing = False
                breath_end_time = new_time
                breath_duration = breath_end_time - self.breath_start_time
                avg_acetone = self.data['acetone'].iloc[-int(breath_duration):].mean()
                messagebox.showinfo("Breathing Segment Complete", f"Average Acetone during breathing: {avg_acetone:.3f} ppm")

            # Check for no breath detected
            if new_acetone <= 0.2:
                self.no_breath_detected += 1
            else:
                self.no_breath_detected = 0

            if self.no_breath_detected > 5:  # If no breath detected for more than 5 seconds
                messagebox.showwarning("Warning", "No breath detected. Please blow again.")
                self.no_breath_detected = 0  # Reset counter after warning

            new_data = pd.DataFrame({
                'time': [new_time],
                'acetone': [new_acetone],
                'error': [new_error],
                'co2': [new_co2]
            })

            # Concatenate new data to the DataFrame
            self.data = pd.concat([self.data, new_data], ignore_index=True)

            # Update the Treeview
            self.tree.insert('', 'end', values=(f"{new_time:.2f}", f"{new_acetone:.3f}", f"{new_error:.3f}", f"{new_co2:.3f}"))

            # Update the plot
            self.plot_data()

            # Delay for the next update
            time.sleep(self.data_update_interval / 1000.0)

    def check_levels(self):
        
        if not self.data.empty and 'acetone' in self.data.columns and len(self.data['acetone']) > 0:
            if self.data['acetone'].iloc[-1] > 1.5:  # 1.5 ppm is used here as an example threshold.
                messagebox.showwarning("Warning", "Acetone levels are too high!")
        else:
            print("Data is empty or 'acetone' column has no data.")
            
            messagebox.showwarning("Warning", "Acetone levels are too high!")

    def plot_data(self):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(self.data['time'], self.data['acetone'], marker='o', label="Acetone Level (ppm)")
        ax.plot(self.data['time'], self.data['co2'], marker='x', label="CO2 Level (ppm)", linestyle='--')
        
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Levels (ppm)")
        ax.set_title("Acetone and CO2 Levels Over Time")
        ax.grid(True)
        ax.legend()
        
        self.clear_plot()
        
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def clear_plot(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = BreathAnalysisApp()
    app.mainloop()
