from typing import Dict, List, Tuple, Optional


UserSessionData = Dict[str, Optional[str]]
UserDataStorage = Dict[int, Dict[str, Optional[str]]]
HistoryEntry = Tuple[str, str, str]
UserHistoryStorage = Dict[int, List[HistoryEntry]]
UtmEditingStorage = Dict[int, Dict[str, Optional[str]]]

# In-memory storages. For now simple dicts are sufficient.
user_data: UserDataStorage = {}
user_history: UserHistoryStorage = {}
utm_editing_data: UtmEditingStorage = {}
