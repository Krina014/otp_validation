from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
from database import users_collection  # Import your MongoDB connection

IST = pytz.timezone("Asia/Kolkata")

def delete_expired_otps():
    """Deletes all OTPs that have expired (past expiration time)."""
    current_time_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

    # Delete all expired OTPs from MongoDB
    deleted_count = users_collection.delete_many({"otp_expiry": {"$lt": current_time_ist}}).deleted_count

    
    if deleted_count:
        print(f"Deleted {deleted_count} expired OTPs data at {current_time_ist}")

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(delete_expired_otps, "interval", seconds=1)  # Run every second
scheduler.start()