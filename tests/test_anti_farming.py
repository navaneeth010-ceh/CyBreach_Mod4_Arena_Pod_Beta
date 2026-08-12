import pytest
from scheduler.anti_farming import AntiFarmingValidator
from datetime import datetime, timedelta

@pytest.fixture(autouse=True)
def clear_redis():
    """Clear Redis before each test"""
    validator = AntiFarmingValidator()
    # Clear all keys with 'cooldown:' prefix
    keys = validator.redis_client.keys('cooldown:*')
    if keys:
        validator.redis_client.delete(*keys)
    yield
    # Cleanup after test
    keys = validator.redis_client.keys('cooldown:*')
    if keys:
        validator.redis_client.delete(*keys)

def test_first_test_allowed():
    """First time running a test should always be approved"""
    validator = AntiFarmingValidator()
    
    can_run, msg, remaining = validator.check_can_run_test("client_001", "sql_injection")
    
    assert can_run == True
    assert "approved" in msg.lower()
    assert remaining == 0

def test_second_test_blocked_within_cooldown():
    """Running same test immediately should be blocked"""
    validator = AntiFarmingValidator()
    validator.set_cooldown(3600)  # 1 hour
    
    # First run
    can_run1, _, _ = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run1 == True
    
    # Immediate second run (should be blocked)
    can_run2, msg, remaining = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run2 == False
    assert "FARMING BLOCKED" in msg
    assert remaining > 3590  # Close to 1 hour

def test_different_test_types_independent():
    """Different test types should have independent cooldowns"""
    validator = AntiFarmingValidator()
    
    # Run SQL injection
    can_run1, _, _ = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run1 == True
    
    # Run XSS test (different test, should be allowed)
    can_run2, msg, _ = validator.check_can_run_test("client_001", "xss_scan")
    assert can_run2 == True
    assert "approved" in msg.lower()

def test_different_clients_independent():
    """Different clients should have independent cooldowns"""
    validator = AntiFarmingValidator()
    
    # Client 1 runs test
    can_run1, _, _ = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run1 == True
    
    # Client 2 runs same test (should be allowed)
    can_run2, msg, _ = validator.check_can_run_test("client_002", "sql_injection")
    assert can_run2 == True

def test_violation_logging():
    """Violations should be logged"""
    validator = AntiFarmingValidator()
    validator.clear_violations()  # Clear any previous violations
    
    # First run (approved)
    validator.check_can_run_test("client_001", "sql_injection")
    
    # Second run (blocked)
    validator.check_can_run_test("client_001", "sql_injection")
    
    violations = validator.get_violations()
    assert len(violations) == 1
    assert violations[0]["client_id"] == "client_001"
    assert violations[0]["test_type"] == "sql_injection"

def test_reset_cooldown():
    """Admin should be able to reset cooldown"""
    validator = AntiFarmingValidator()
    
    # First run
    validator.check_can_run_test("client_001", "sql_injection")
    
    # Second run (blocked)
    can_run2, _, _ = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run2 == False
    
    # Reset cooldown
    validator.reset_client_cooldown("client_001", "sql_injection")
    
    # Now should be allowed
    can_run3, msg, _ = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run3 == True

def test_custom_cooldown_period():
    """Should support custom cooldown durations"""
    validator = AntiFarmingValidator()
    validator.set_cooldown(10)  # 10 seconds instead of 1 hour
    
    # First run
    validator.check_can_run_test("client_001", "sql_injection")
    
    # Second run (blocked)
    can_run2, msg, remaining = validator.check_can_run_test("client_001", "sql_injection")
    assert can_run2 == False
    assert remaining > 0 and remaining <= 10

def test_multiple_violations():
    """Should track multiple violations"""
    validator = AntiFarmingValidator()
    validator.clear_violations()  # Start fresh
    
    # Client 1 tries twice
    validator.check_can_run_test("client_001", "sql_injection")
    validator.check_can_run_test("client_001", "sql_injection")
    
    # Client 2 tries twice
    validator.check_can_run_test("client_002", "xss_scan")
    validator.check_can_run_test("client_002", "xss_scan")
    
    violations = validator.get_violations()
    assert len(violations) == 2

def test_clear_violations():
    """Should be able to clear violation log"""
    validator = AntiFarmingValidator()
    validator.clear_violations()  # Start fresh
    
    validator.check_can_run_test("client_001", "sql_injection")
    validator.check_can_run_test("client_001", "sql_injection")
    
    assert len(validator.get_violations()) == 1
    
    validator.clear_violations()
    assert len(validator.get_violations()) == 0