from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime
import uuid

class AutomationScheduler:
    def __init__(self):
        """Initialize the background scheduler with in-memory job storage"""
        jobstores = {
            'default': MemoryJobStore()
        }
        
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.jobs_log = []  # Track all scheduled jobs
        
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("✅ Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("✅ Scheduler stopped")
    
    def schedule_daily_test(self, client_id: str, test_type: str, hour: int = 9, minute: int = 0):
        """
        Schedule a recurring daily security test
        
        Args:
            client_id: Unique client identifier
            test_type: Type of test (e.g., "sql_injection", "xss_scan")
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        job_id = f"{client_id}_{test_type}_{uuid.uuid4()}"
        
        def run_test():
            execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "job_id": job_id,
                "client_id": client_id,
                "test_type": test_type,
                "executed_at": execution_time
            }
            self.jobs_log.append(log_entry)
            print(f"🔥 Test triggered: {test_type} for client {client_id}")
        
        self.scheduler.add_job(
            run_test,
            'cron',
            hour=hour,
            minute=minute,
            id=job_id,
            name=f"Daily {test_type} for {client_id}"
        )
        
        return job_id
    
    def schedule_weekly_test(self, client_id: str, test_type: str, day_of_week: int = 0, hour: int = 9):
        """
        Schedule a recurring weekly security test
        
        Args:
            client_id: Unique client identifier
            test_type: Type of test
            day_of_week: 0=Monday, 1=Tuesday, etc.
            hour: Hour to run
        """
        job_id = f"{client_id}_{test_type}_weekly_{uuid.uuid4()}"
        
        def run_test():
            execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "job_id": job_id,
                "client_id": client_id,
                "test_type": test_type,
                "executed_at": execution_time
            }
            self.jobs_log.append(log_entry)
            print(f"🔥 Weekly test triggered: {test_type} for client {client_id}")
        
        self.scheduler.add_job(
            run_test,
            'cron',
            day_of_week=day_of_week,
            hour=hour,
            id=job_id,
            name=f"Weekly {test_type} for {client_id}"
        )
        
        return job_id
    
    def get_all_jobs(self):
        """Return list of all scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def get_execution_log(self):
        """Return log of all executed tests"""
        return self.jobs_log
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        self.scheduler.remove_job(job_id)
        print(f"❌ Job removed: {job_id}")