import os
import sys
import tempfile
import re
import pygame
import tkinter as tk
from tkinter import ttk
import getpass
from datetime import datetime
from cron_manager import *


class AlarmSystem:
    def __init__(self):
        self.cron = CronManager()
        self.alarm_prefix = "WEB_ALARM_"
        self.sound_file = self._get_sound_file()
        self.current_alarm_time = None
        
    def _get_sound_file(self):
        """Locate alarm sound file with fallbacks"""
        project_dir = os.path.dirname(os.path.abspath(__file__))
        custom_sound = os.path.join(project_dir, "sounds", "alarm.mp3")
        
        if os.path.exists(custom_sound):
            return custom_sound
        
        # System sound fallbacks
        fallbacks = [
            "/usr/share/sounds/ubuntu/notifications/Amsterdam.ogg",
            "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "/usr/share/sounds/alsa/Front_Center.wav"
        ]
        
        for sound in fallbacks:
            if os.path.exists(sound):
                return sound
        
        return None  # No sound available
    def set_alarm(self, hour, minute, message="Alarm!"):
        time_str = f"{hour:02d}{minute:02d}"
        comment = f"{self.alarm_prefix}{time_str}"
        
        # Get absolute paths
        project_dir = os.path.dirname(os.path.abspath(__file__))
        launcher = os.path.join(project_dir, "alarm_launcher.sh")
        
        # Build the cron command with proper escaping
        quoted_message = message.replace("'", "'\"'\"'")
        command = f"/bin/bash {launcher} {time_str} '{quoted_message}'"
        
        schedule = f"{minute} {hour} * * *"
        return self.cron.add_job(
            cron_command=command,
            schedule=schedule,
            comment=comment
        )

        
    def trigger_alarm(self, message):
        try:
            # Initialize audio system
            os.environ['SDL_AUDIODRIVER'] = 'pulse'
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
            # Play sound if available
            if self.sound_file and os.path.exists(self.sound_file):
                try:
                    pygame.mixer.music.load(self.sound_file)
                    pygame.mixer.music.play(loops=-1)
                except Exception as e:
                    print(f"Sound error: {e}")
                    os.system(f'notify-send "Alarm Sound Error" "{str(e)}"')

            # Create main window
            root = tk.Tk()
            root.title("⏰ ALARM!")
            root.attributes('-topmost', True)
            root.configure(bg='black')
            
            # Make window fullscreen but with escape option
            root.attributes('-fullscreen', True)
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Create alarm frame
            alarm_frame = tk.Frame(root, bg='#FF4444', padx=20, pady=20)
            alarm_frame.place(relx=0.5, rely=0.5, anchor='center')
            
            # Alarm message
            msg_label = tk.Label(
                alarm_frame,
                text=message,
                font=('Helvetica', 24, 'bold'),
                fg='white',
                bg='#FF4444',
                wraplength=screen_width*0.8
            )
            msg_label.pack(pady=20)
            
            # Time display
            time_str = datetime.now().strftime("%H:%M:%S")
            time_label = tk.Label(
                alarm_frame,
                text=time_str,
                font=('Helvetica', 36, 'bold'),
                fg='white',
                bg='#FF4444'
            )
            time_label.pack(pady=10)
            
            # Button frame
            button_frame = tk.Frame(alarm_frame, bg='#FF4444')
            button_frame.pack(pady=20)
            
            # Stop button
            stop_btn = tk.Button(
                button_frame,
                text="STOP",
                font=('Helvetica', 18),
                bg='#AA0000',
                fg='white',
                activebackground='#880000',
                command=lambda: self._stop_alarm(root)
            )
            stop_btn.pack(side='left', padx=10)
            
            # Snooze button
            snooze_btn = tk.Button(
                button_frame,
                text="SNOOZE (5 min)",
                font=('Helvetica', 18),
                bg='#0066AA',
                fg='white',
                activebackground='#004488',
                command=lambda: self._snooze_alarm(root)
            )
            snooze_btn.pack(side='left', padx=10)
            
            # Update time display
            def update_time():
                time_label.config(text=datetime.now().strftime("%H:%M:%S"))
                root.after(1000, update_time)
            
            update_time()
            root.mainloop()

        except Exception as e:
            print(f"Alarm error: {e}")
            os.system(f'notify-send "Alarm Failed" "{str(e)}"')
        finally:
            if pygame.mixer.get_init():
                pygame.mixer.quit()

    def _snooze_alarm(self, window):
        """Snooze alarm for 5 minutes"""
        if self.current_alarm_time:
            try:
                hour, minute = int(self.current_alarm_time[:2]), int(self.current_alarm_time[2:])
                new_minute = (minute + 5) % 60
                new_hour = (hour + (minute + 5) // 60) % 24
                
                # Cancel original alarm
                self.cancel_alarm(hour, minute)
                
                # Set new alarm
                self.set_alarm(new_hour, new_minute, "Snoozed Alarm")
                
                # Close current window
                self._stop_alarm(window)
                
                os.system(f'notify-send "Alarm Snoozed" "New alarm at {new_hour:02d}:{new_minute:02d}"')
            except Exception as e:
                print(f"Snooze error: {e}")

    def _stop_alarm(self, window):
        """Clean up alarm resources"""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        if window:
            window.destroy()

    def cancel_alarm(self, hour, minute):
        """Cancel specific alarm"""
        comment = f"{self.alarm_prefix}{hour:02d}{minute:02d}"
        return self.cron.remove_job(comment)

if __name__ == "__main__":
    # Initialize essential components
    pygame.init()
    if not os.environ.get('DISPLAY'):
        os.environ['DISPLAY'] = ':0'
    
    # Handle command line trigger
    if len(sys.argv) > 2 and sys.argv[1] == "--trigger":
        alarm = AlarmSystem()
        alarm.current_alarm_time = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else "Alarm!"
        alarm.trigger_alarm(message)
