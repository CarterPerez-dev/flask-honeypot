# honeypot/database/models.py
from datetime import datetime
from bson.objectid import ObjectId

class HoneypotModel:
    """Base model for honeypot data objects"""
    
    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance

class HoneypotInteraction:
    """Model for storing honeypot interactions"""
    
    def __init__(self, page_type=None, interaction_type=None, 
                 ip_address=None, user_agent=None, path=None, 
                 timestamp=None, additional_data=None, **kwargs):
        self.id = str(ObjectId())
        self.page_type = page_type
        self.interaction_type = interaction_type
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.path = path
        self.timestamp = timestamp or datetime.utcnow()
        self.additional_data = additional_data or {}
        
        # Additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "_id": ObjectId(self.id) if isinstance(self.id, str) else self.id,
            "page_type": self.page_type,
            "interaction_type": self.interaction_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "path": self.path,
            "timestamp": self.timestamp,
            "additional_data": self.additional_data
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from MongoDB document"""
        if data is None:
            return None
            
        obj = cls()
        obj.id = str(data.get("_id", ""))
        obj.page_type = data.get("page_type")
        obj.interaction_type = data.get("interaction_type")
        obj.ip_address = data.get("ip_address")
        obj.user_agent = data.get("user_agent")
        obj.path = data.get("path")
        obj.timestamp = data.get("timestamp")
        obj.additional_data = data.get("additional_data", {})
        
        return obj

class ScanAttempt:
    """Model for tracking scanning attempts"""
    
    def __init__(self, client_id=None, ip=None, path=None, method=None,
                 timestamp=None, user_agent=None, headers=None, 
                 asn_info=None, **kwargs):
        self.id = str(ObjectId())
        self.client_id = client_id
        self.ip = ip
        self.path = path
        self.method = method
        self.timestamp = timestamp or datetime.utcnow()
        self.user_agent = user_agent
        self.headers = headers or {}
        self.asn_info = asn_info or {}
        
        # Additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "_id": ObjectId(self.id) if isinstance(self.id, str) else self.id,
            "clientId": self.client_id,
            "ip": self.ip,
            "path": self.path,
            "method": self.method,
            "timestamp": self.timestamp,
            "user_agent": self.user_agent,
            "headers": self.headers,
            "asn_info": self.asn_info
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from MongoDB document"""
        if data is None:
            return None
            
        obj = cls()
        obj.id = str(data.get("_id", ""))
        obj.client_id = data.get("clientId")
        obj.ip = data.get("ip")
        obj.path = data.get("path")
        obj.method = data.get("method")
        obj.timestamp = data.get("timestamp")
        obj.user_agent = data.get("user_agent")
        obj.headers = data.get("headers", {})
        obj.asn_info = data.get("asn_info", {})
        
        return obj

class WatchlistEntry:
    """Model for tracking suspicious activity"""
    
    def __init__(self, client_id=None, ip=None, last_seen=None, count=0, 
                 severity=0, last_path=None, **kwargs):
        self.id = str(ObjectId())
        self.client_id = client_id
        self.ip = ip
        self.last_seen = last_seen or datetime.utcnow()
        self.count = count
        self.severity = severity
        self.last_path = last_path
        
        # Additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "_id": ObjectId(self.id) if isinstance(self.id, str) else self.id,
            "clientId": self.client_id,
            "ip": self.ip,
            "lastSeen": self.last_seen,
            "count": self.count,
            "severity": self.severity,
            "lastPath": self.last_path
        }

class BlocklistEntry:
    """Model for IP/client blocklist"""
    
    def __init__(self, client_id=None, ip=None, block_until=None, 
                 reason=None, threat_score=0, **kwargs):
        self.id = str(ObjectId())
        self.client_id = client_id
        self.ip = ip
        self.block_until = block_until
        self.reason = reason
        self.threat_score = threat_score
        self.created_at = datetime.utcnow()
        
        # Additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "_id": ObjectId(self.id) if isinstance(self.id, str) else self.id,
            "clientId": self.client_id,
            "ip": self.ip,
            "blockUntil": self.block_until,
            "reason": self.reason,
            "threatScore": self.threat_score,
            "createdAt": self.created_at
        }
