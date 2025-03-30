# cron_manager.py
import os
import tempfile
import re

class CronManager:
    """Unified cron job management class"""
    
    @staticmethod
    def validate_schedule(schedule):
        """Validate cron schedule format"""
        pattern = r'^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3])) (\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/([1-9]|1[0-9]|2[0-9]|3[0-1])) (\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2])) (\*|([0-6])|\*\/([0-6]))$'
        return re.match(pattern, schedule) is not None

    def cron_job_exists(self,comment):
        """
        Check if a cron job with specific comment exists
        
        Args:
            comment (str): The comment text to search for (without #)
        Returns:
            bool: True if comment exists, False otherwise
        """
        try:
            cron_content = os.popen("crontab -l 2>/dev/null").read()
            return f"# {comment}" in cron_content
        except Exception as e:
            print(f"Error checking cron jobs: {e}")
            return False

    def add_job(self,cron_command, schedule, comment=None):
        """
        Add a cron job using explicit filename with duplicate comment checking
        
        Args:
            cron_command (str): Command to execute
            schedule (str): Cron schedule (e.g., "*/10 * * * *")
            comment (str, optional): Description for the job (must be unique)
        
        Returns:
            bool: True if job was added successfully, False otherwise
        
        Raises:
            Exception: If comment already exists or other errors occur
        """
        # First check for duplicate comments
        if comment:
            existing_cron = os.popen("crontab -l 2>/dev/null").read()
            if f"# {comment}" in existing_cron:
                raise Exception(f"Comment '{comment}' already exists in crontab")

        cron_job = f"{schedule} {cron_command}"
        if comment:
            cron_job = f"# {comment}\n{cron_job}"
        
        cron_file = "/tmp/user_cron_jobs.tmp"  # Fixed filename
        
        try:
            # Read existing crontab
            exit_code = os.system(f"crontab -l > {cron_file} 2>/dev/null")
            if exit_code not in [0, 256]:  # 256 = no crontab exists
                raise Exception("Failed to read existing crontab")
            
            # Append new job
            with open(cron_file, "a") as f:
                f.write(cron_job + "\n")
            
            # Install new crontab
            if os.system(f"crontab {cron_file}") != 0:
                raise Exception("Failed to install new crontab")
            
            print(f"✓ Cron job added with comment: '{comment}'" if comment else "✓ Cron job added")
            return True
        
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            if os.path.exists(cron_file):
                os.remove(cron_file)

    def update_job(self, comment, new_schedule):
        """
        Update the schedule of a cron job identified by its comment
        
        Args:
            comment (str): The comment text (without #) that identifies the job
            new_schedule (str): The new cron schedule (e.g., "*/5 * * * *")
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not a.cron_job_exists(comment):
            print(f"Error: No cron job found with comment '{comment}'")
            return False
            
        if not a.validate_schedule(new_schedule):
            print(f"Error: Invalid cron schedule format '{new_schedule}'")
            return False
    
        try:
            # Get current crontab content
            cron_content = os.popen("crontab -l 2>/dev/null").read().splitlines()
            
            new_cron_content = []
            updated = False
            
            i = 0
            while i < len(cron_content):
                line = cron_content[i].strip()
                
                # Check for our comment
                if line == f"# {comment}":
                    # Add the comment line
                    new_cron_content.append(cron_content[i])
                    
                    # Find the next non-comment, non-empty line (the command)
                    i += 1
                    while i < len(cron_content):
                        cmd_line = cron_content[i].strip()
                        if cmd_line and not cmd_line.startswith('#'):
                            # Split into schedule and command
                            parts = cmd_line.split()
                            if len(parts) >= 6:  # 5 schedule parts + command
                                command = ' '.join(parts[5:])
                                new_line = f"{new_schedule} {command}"
                                new_cron_content.append(new_line)
                                updated = True
                            break
                        new_cron_content.append(cron_content[i])
                        i += 1
                else:
                    new_cron_content.append(cron_content[i])
                
                i += 1
            
            if not updated:
                print(f"Error: Found comment but couldn't find command for '{comment}'")
                return False
            
            # Write the updated content
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
                tmp.write("\n".join(new_cron_content))
                if new_cron_content:
                    tmp.write("\n")  # Ensure trailing newline
                tmp_path = tmp.name
            
            # Install new crontab
            if os.system(f"crontab {tmp_path}") != 0:
                raise Exception("Failed to update crontab")
            
            print(f"✓ Successfully updated schedule for '{comment}' to '{new_schedule}'")
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def remove_job(self, comment):
        """
        Removes cron job by comment and all subsequent lines until next comment
        
        Args:
            comment (str): The comment text (without #) that identifies job to remove
        """
        try:
            # Get current crontab content
            cron_content = os.popen("crontab -l 2>/dev/null").read().splitlines()
            
            # Process lines to remove target job and subsequent commands
            new_cron_content = []
            in_removal = False
            removed = False
            
            for line in cron_content:
                stripped_line = line.strip()
                
                # Check if this is any comment line
                if stripped_line.startswith('#'):
                    # If we're in removal, stop at next comment
                    if in_removal:
                        in_removal = False
                    
                    # Check if this is our target comment
                    if stripped_line == f"# {comment}":
                        in_removal = True
                        removed = True
                        continue
                
                # Only keep lines not marked for removal
                if not in_removal:
                    new_cron_content.append(line)
            
            # Write the filtered content
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
                tmp.write("\n".join(new_cron_content))
                if new_cron_content:  # Add trailing newline if content exists
                    tmp.write("\n")
                tmp_path = tmp.name
            
            # Install new crontab
            if os.system(f"crontab {tmp_path}") != 0:
                raise Exception("Failed to update crontab")
            
            if removed:
                print(f"✓ Removed job with comment '{comment}' and subsequent commands")
            else:
                print(f"⚠ No job found with comment '{comment}'")
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)


    @staticmethod
    def list_jobs():
        """List all cron jobs"""
        return os.popen("crontab -l 2>/dev/null").read()
a=CronManager()
