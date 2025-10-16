from typing import Dict, Optional, Set


UserSessionData = Dict[str, Optional[str]]
UserDataStorage = Dict[int, Dict[str, Optional[str]]]
UtmEditingStorage = Dict[int, Dict[str, Optional[str]]]
PendingAuthUsers = Set[int]

# In-memory storages. For now simple dicts are sufficient.
user_data: UserDataStorage = {}
utm_editing_data: UtmEditingStorage = {}
pending_password_users: PendingAuthUsers = set()
