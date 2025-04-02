# alarm_system.py
from cron_manager import CronManager
import os
import sys
import tkinter as tk
from tkinter import ttk
import time
import pygame
from datetime import datetime, timedelta

class AlarmPopup:
    def __init__(self, message, sound_file):
        self.root = tk.Tk()
        self.root.title("Alarm Notification")
        self.sound_file = sound_file
        self.sound_playing = False
        
        # Set DISPLAY environment variable if not set
        if not os.environ.get('DISPLAY'):
            os.environ['DISPLAY'] = ':0'
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Window styling
        self.root.configure(bg='#f0f0f0')
        self.root.attributes('-topmost', True)
        
        # Center window
        window_width = 400
        window_height = 200
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Message label
        lbl_message = ttk.Label(
            self.root,
            text=message,
            font=('Helvetica', 14),
            wraplength=350,
            justify='center',
            background='#f0f0f0'
        )
        lbl_message.pack(pady=20)
        
        # Button frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        # Snooze button
        btn_snooze = ttk.Button(
            btn_frame,
            text="Snooze (5 min)",
            command=self.snooze,
            width=15
        )
        btn_snooze.pack(side=tk.LEFT, padx=10)
        
        # Cancel button
        btn_cancel = ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.cancel,
            width=15
        )
        btn_cancel.pack(side=tk.LEFT, padx=10)
        
        # Start playing sound
        self.play_sound()
        
        # Focus the window
        self.root.focus_force()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Update the sound loop
        self.update_sound()
        
        self.root.mainloop()
    
    def play_sound(self):
        """Play alarm sound using pygame"""
        if os.path.exists(self.sound_file):
            try:
                pygame.mixer.music.load(self.sound_file)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                self.sound_playing = True
            except Exception as e:
                print(f"Error playing sound: {e}")
    
    def update_sound(self):
        """Maintain sound playback"""
        if self.sound_playing and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        self.root.after(100, self.update_sound)
    
    def stop_sound(self):
        """Stop the alarm sound"""
        if self.sound_playing:
            pygame.mixer.music.stop()
            self.sound_playing = False
    
    def snooze(self):
        """Snooze the alarm for 5 minutes"""
        self.stop_sound()
        self.root.destroy()
        # Recreate the alarm in 5 minutes
        AlarmSystem().snooze_current()
    
    def cancel(self):
        """Cancel the alarm"""
        self.stop_sound()
        self.root.destroy()

class AlarmSystem:
    def __init__(self):
        self.cron = CronManager()
        self.alarm_prefix = "ALARM_"
        self.sound_file = "/home/phoenix/Faded.mp3"
        self.current_alarm_time = None
    
    def set_alarm(self, hour, minute, message="Alarm!"):
        """Set a new alarm"""
        self.current_alarm_time = f"{hour:02d}{minute:02d}"
        comment = f"{self.alarm_prefix}{self.current_alarm_time}"
        
        # Command to trigger this script with proper environment
        script_path = os.path.abspath(__file__)
        command = f"export DISPLAY=:0 && python3 {script_path} --trigger {self.current_alarm_time} '{message}'"
        
        # Set the cron job
        schedule = f"{minute} {hour} * * *"
        try:
            self.cron.add_job(
                cron_command=command,
                schedule=schedule,
                comment=comment
            )
            print(f"⏰ Alarm set for {hour:02d}:{minute:02d} daily")
        except Exception as e:
            print(f"Failed to set alarm: {e}")
    
    def snooze_current(self):
        """Snooze the current alarm for 5 minutes"""
        if not self.current_alarm_time:
            print("No alarm to snooze")
            return
        
        # Calculate snooze time (current time + 5 minutes)
        now = datetime.now()
        snooze_time = now + timedelta(minutes=5)
        
        # Set temporary snooze alarm
        temp_comment = f"SNOOZE_{self.current_alarm_time}"
        script_path = os.path.abspath(__file__)
        command = f"export DISPLAY=:0 && python3 {script_path} --trigger {self.current_alarm_time}"
        
        try:
            self.cron.add_job(
                cron_command=command,
                schedule=f"{snooze_time.minute} {snooze_time.hour} * * *",
                comment=temp_comment
            )
            print(f"⏰ Alarm snoozed until {snooze_time.hour:02d}:{snooze_time.minute:02d}")
        except Exception as e:
            print(f"Failed to snooze alarm: {e}")
    
    def trigger_alarm(self, message):
        """Trigger the alarm popup"""
        AlarmPopup(message, self.sound_file)
    
    def list_alarms(self):
        """List all set alarms"""
        jobs = self.cron.list_jobs()
        if not jobs or "No cron jobs exist" in jobs:
            print("No alarms currently set")
            return
        
        print("Current Alarms:")
        for line in jobs.splitlines():
            if self.alarm_prefix in line and "SNOOZE_" not in line:
                time_part = line.split(self.alarm_prefix)[1].strip()
                hour, minute = time_part[:2], time_part[2:4]
                print(f"- {hour}:{minute}")
    
    def cancel_alarm(self, hour, minute):
        """Cancel specific alarm"""
        comment = f"{self.alarm_prefix}{hour:02d}{minute:02d}"
        try:
            self.cron.remove_job(comment)
            print(f"Alarm at {hour:02d}:{minute:02d} cancelled")
        except Exception as e:
            print(f"Failed to cancel alarm: {e}")
    
    def cancel_all_alarms(self):
        """Cancel all alarms and snoozes"""
        jobs = self.cron.list_jobs()
        if not jobs or "No cron jobs exist" in jobs:
            print("No alarms to cancel")
            return
        
        cancelled = 0
        for line in jobs.splitlines():
            if self.alarm_prefix in line:
                time_part = line.split(self.alarm_prefix)[1].strip()
                hour, minute = time_part[:2], time_part[2:4]
                self.cancel_alarm(int(hour), int(minute))
                cancelled += 1
        
        print(f"Cancelled {cancelled} alarms")

if __name__ == "__main__":
    # Initialize pygame
    pygame.init()
    
    alarm = AlarmSystem()
    
    # Handle alarm triggering
    if len(sys.argv) > 2 and sys.argv[1] == "--trigger":
        alarm_code = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else "Alarm!"
        alarm.current_alarm_time = alarm_code
        
        # Ensure we have proper environment for GUI
        if not os.environ.get('DISPLAY'):
            os.environ['DISPLAY'] = ':0'
        
        alarm.trigger_alarm(message)
    else:
        # Interactive menu
        while True:
            print("\nAlarm System Menu:")
            print("1. Set Alarm")
            print("2. List Alarms")
            print("3. Cancel Alarm")
            print("4. Cancel All Alarms")
            print("5. Exit")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == "1":
                try:
                    hour = int(input("Enter hour (0-23): "))
                    minute = int(input("Enter minute (0-59): "))
                    message = input("Enter alarm message (optional): ")
                    alarm.set_alarm(hour, minute, message or "Alarm!")
                except ValueError:
                    print("Please enter valid numbers")
            elif choice == "2":
                alarm.list_alarms()
            elif choice == "3":
                try:
                    hour = int(input("Enter hour to cancel (0-23): "))
                    minute = int(input("Enter minute to cancel (0-59): "))
                    alarm.cancel_alarm(hour, minute)
                except ValueError:
                    print("Please enter valid numbers")
            elif choice == "4":
                alarm.cancel_all_alarms()
            elif choice == "5":
                pygame.quit()
                break
            else:
                print("Invalid choice")
