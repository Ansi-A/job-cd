from enum import Enum
class DeploymentStatus(str, Enum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    CONTACTS_FOUND = "contacts_found"
    DRAFTED = "drafted"
    PARTIALLY_DRAFTED = "partially_drafted"
    SENT = "sent"
    PARTIALLY_SENT = "partially_sent"
    FAILED = "failed"