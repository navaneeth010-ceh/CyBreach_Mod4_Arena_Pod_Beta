from redis import Redis
from datetime import datetime, timedelta
import time

class AntiFarmingValidator:
    def __init__(self, redis_host='localhost', redis_port=6379):
        """Initialize connection to Redis (in Docker)"""
        self.redis_client = Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True  # Return strings, not bytes
        )
        self.cooldown_seconds = 3600  # 1 hour cooldown
        self.violation_log = []
    
    def set_cooldown(self, cooldown_seconds: int):
        """Change the cooldown period (default 1 hour)"""
        self.cooldown_seconds = cooldown_seconds
    
    def check_can_run_test(self, client_id: str, test_type: str) -> tuple[bool, str, int]:
        """
        Check if a client can run a test or if they're in cooldown
        
        Returns:
            (can_run, message, seconds_remaining)
        """
        # Create unique key for this client + test type
        key = f"cooldown:{client_id}:{test_type}"
        
        # Check if key exists in Redis (means they ran it recently)
        last_run_timestamp = self.redis_client.get(key)
        
        if last_run_timestamp is None:
            # First time running this test, allow it
            now = datetime.now().isoformat()
            self.redis_client.set(
                key,
                now,
                ex=self.cooldown_seconds
            )
            return True, f"✅ Test approved: {test_type}", 0
        
        # They ran it before, check cooldown
        last_run = datetime.fromisoformat(last_run_timestamp)
        now = datetime.now()
        time_elapsed = (now - last_run).total_seconds()
        time_remaining = self.cooldown_seconds - time_elapsed
        
        if time_remaining > 0:
            # Still in cooldown period
            violation = {
                "client_id": client_id,
                "test_type": test_type,
                "last_run": last_run_timestamp,
                "blocked_at": now.isoformat(),
                "seconds_remaining": int(time_remaining)
            }
            self.violation_log.append(violation)
            
            return False, (
                f"❌ FARMING BLOCKED: {test_type} cooldown active. "
                f"Wait {int(time_remaining)} more seconds"
            ), int(time_remaining)
        
        # Cooldown expired, allow new run
        now = datetime.now().isoformat()
        self.redis_client.setex(key, self.cooldown_seconds, now)
        return True, f"✅ Cooldown expired, test approved: {test_type}", 0
    
    def reset_client_cooldown(self, client_id: str, test_type: str = None):
        """
        Manually reset cooldown for a client (admin function)
        If test_type is None, reset ALL tests for that client
        """
        if test_type:
            key = f"cooldown:{client_id}:{test_type}"
            self.redis_client.delete(key)
            return f"✅ Cooldown reset for {client_id}:{test_type}"
        else:
            # Reset all tests for this client
            pattern = f"cooldown:{client_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return f"✅ All cooldowns reset for {client_id}"
    
    def get_violations(self):
        """Return all farming attempts"""
        return self.violation_log
    
    def clear_violations(self):
        """Clear violation log"""
        self.violation_log = []
    
    def get_redis_stats(self):
        """Get info about Redis server"""
        return self.redis_client.info()