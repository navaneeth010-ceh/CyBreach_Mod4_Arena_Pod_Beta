from pydantic import BaseModel, Field
from typing import Dict

class ScopeContract(BaseModel):
    """Defines a client's testing scope limits"""
    client_id: str
    baseline_asset_count: int = Field(gt=0)  # Must be > 0
    asset_type: str  # e.g., "domains", "ips", "subdomains"
    
    @property
    def max_allowed_assets(self):
        """Calculate 120% of baseline"""
        return int(self.baseline_asset_count * 1.2)

class ScopeDriftValidator:
    def __init__(self):
        """Initialize validator with contract storage"""
        self.contracts: Dict[str, ScopeContract] = {}
        self.violation_log = []
    
    def register_contract(self, client_id: str, baseline_asset_count: int, asset_type: str = "domains"):
        """Register a client's scope contract"""
        contract = ScopeContract(
            client_id=client_id,
            baseline_asset_count=baseline_asset_count,
            asset_type=asset_type
        )
        self.contracts[client_id] = contract
        return contract
    
    def validate_scope(self, client_id: str, requested_asset_count: int) -> tuple[bool, str]:
        """
        Validate if requested assets stay within 120% scope limit
        
        Returns:
            (is_valid, message)
        """
        if client_id not in self.contracts:
            return False, f"❌ Client {client_id} not found in contracts"
        
        contract = self.contracts[client_id]
        max_allowed = contract.max_allowed_assets
        
        if requested_asset_count <= max_allowed:
            return True, f"✅ Scope approved: {requested_asset_count} assets (max: {max_allowed})"
        
        # VIOLATION: Scope drift detected
        drift_percentage = (requested_asset_count / contract.baseline_asset_count) * 100
        violation = {
            "client_id": client_id,
            "requested_assets": requested_asset_count,
            "max_allowed": max_allowed,
            "baseline": contract.baseline_asset_count,
            "drift_percentage": drift_percentage
        }
        self.violation_log.append(violation)
        
        return False, (
            f"❌ SCOPE DRIFT VIOLATION: Requested {requested_asset_count} assets "
            f"exceeds maximum {max_allowed} (baseline: {contract.baseline_asset_count}, "
            f"drift: {drift_percentage:.1f}%)"
        )
    
    def get_violations(self):
        """Return all scope drift violations"""
        return self.violation_log
    
    def reset_violations(self):
        """Clear violation log"""
        self.violation_log = []