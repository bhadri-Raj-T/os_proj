from cron_manager import *
cron=CronManager()

#creating
"""
cron.add_job(
    cron_command="echo 'Hi there' >> '/home/phoenix/Desktop/23MIA1029/OSproj/text.txt'",
    schedule="* * * * *",
    comment="Sample"
)

cron.add_job(
    cron_command="echo 'Hello there' >> '/home/phoenix/Desktop/23MIA1029/OSproj/text.txt'",
    schedule="*/2 * * * *",
    comment="Sample2"
)
"""

#removing
"""
cron.remove_job("Sample")
"""

#modify
"""
cron.update_job("Sample","*/2 * * * *")
"""

#listing
print(cron.list_jobs())

