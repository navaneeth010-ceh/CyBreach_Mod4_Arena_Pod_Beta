import pytest
from scheduler.automation_engine import AutomationScheduler
from time import sleep

def test_scheduler_starts_and_stops():
    """Test that scheduler can start and stop"""
    scheduler = AutomationScheduler()
    scheduler.start()
    assert scheduler.scheduler.running == True
    
    scheduler.stop()
    assert scheduler.scheduler.running == False

def test_schedule_daily_test():
    """Test that daily test can be scheduled"""
    scheduler = AutomationScheduler()
    scheduler.start()
    
    job_id = scheduler.schedule_daily_test(
        client_id="client_001",
        test_type="sql_injection",
        hour=9,
        minute=0
    )
    
    jobs = scheduler.get_all_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == job_id
    
    scheduler.stop()

def test_schedule_weekly_test():
    """Test that weekly test can be scheduled"""
    scheduler = AutomationScheduler()
    scheduler.start()
    
    job_id = scheduler.schedule_weekly_test(
        client_id="client_002",
        test_type="xss_scan",
        day_of_week=0,  # Monday
        hour=10
    )
    
    jobs = scheduler.get_all_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == job_id
    
    scheduler.stop()

def test_multiple_jobs():
    """Test scheduling multiple jobs for different clients"""
    scheduler = AutomationScheduler()
    scheduler.start()
    
    job1 = scheduler.schedule_daily_test("client_001", "sql_injection")
    job2 = scheduler.schedule_daily_test("client_002", "xss_scan")
    job3 = scheduler.schedule_weekly_test("client_003", "csrf_check")
    
    jobs = scheduler.get_all_jobs()
    assert len(jobs) == 3
    
    scheduler.stop()

def test_remove_job():
    """Test that jobs can be removed"""
    scheduler = AutomationScheduler()
    scheduler.start()
    
    job_id = scheduler.schedule_daily_test("client_001", "sql_injection")
    assert len(scheduler.get_all_jobs()) == 1
    
    scheduler.remove_job(job_id)
    assert len(scheduler.get_all_jobs()) == 0
    
    scheduler.stop()