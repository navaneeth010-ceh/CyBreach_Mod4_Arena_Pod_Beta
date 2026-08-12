import pytest
from scheduler.scope_drift import ScopeDriftValidator, ScopeContract

def test_contract_creation():
    """Test that scope contracts are created correctly"""
    validator = ScopeDriftValidator()
    contract = validator.register_contract(
        client_id="client_001",
        baseline_asset_count=100,
        asset_type="domains"
    )
    
    assert contract.client_id == "client_001"
    assert contract.baseline_asset_count == 100
    assert contract.max_allowed_assets == 120  # 100 * 1.2

def test_scope_within_limit():
    """Test that requests within 120% are approved"""
    validator = ScopeDriftValidator()
    validator.register_contract("client_001", baseline_asset_count=100)
    
    # Test at baseline
    is_valid, msg = validator.validate_scope("client_001", 100)
    assert is_valid == True
    assert "approved" in msg.lower()
    
    # Test at 120% limit
    is_valid, msg = validator.validate_scope("client_001", 120)
    assert is_valid == True

def test_scope_exceeds_limit():
    """Test that requests exceeding 120% are rejected"""
    validator = ScopeDriftValidator()
    validator.register_contract("client_001", baseline_asset_count=100)
    
    # Try 121 assets (exceeds 120 max)
    is_valid, msg = validator.validate_scope("client_001", 121)
    assert is_valid == False
    assert "SCOPE DRIFT VIOLATION" in msg
    assert "121" in msg

def test_violation_logging():
    """Test that violations are logged"""
    validator = ScopeDriftValidator()
    validator.register_contract("client_001", baseline_asset_count=100)
    
    # Trigger violation
    validator.validate_scope("client_001", 200)
    
    violations = validator.get_violations()
    assert len(violations) == 1
    assert violations[0]["requested_assets"] == 200
    assert violations[0]["max_allowed"] == 120

def test_multiple_clients():
    """Test scope drift for multiple clients with different limits"""
    validator = ScopeDriftValidator()
    validator.register_contract("client_001", baseline_asset_count=100)
    validator.register_contract("client_002", baseline_asset_count=50)
    
    # Client 1: 100 baseline, max 120
    is_valid1, _ = validator.validate_scope("client_001", 120)
    assert is_valid1 == True
    
    # Client 2: 50 baseline, max 60
    is_valid2, _ = validator.validate_scope("client_002", 60)
    assert is_valid2 == True
    
    # Client 2 tries to exceed
    is_valid3, _ = validator.validate_scope("client_002", 61)
    assert is_valid3 == False

def test_unknown_client():
    """Test that unknown clients are rejected"""
    validator = ScopeDriftValidator()
    
    is_valid, msg = validator.validate_scope("unknown_client", 100)
    assert is_valid == False
    assert "not found" in msg.lower()

def test_reset_violations():
    """Test that violation log can be reset"""
    validator = ScopeDriftValidator()
    validator.register_contract("client_001", baseline_asset_count=100)
    
    validator.validate_scope("client_001", 200)
    assert len(validator.get_violations()) == 1
    
    validator.reset_violations()
    assert len(validator.get_violations()) == 0