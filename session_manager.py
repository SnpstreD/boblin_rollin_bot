import time
import threading
from typing import Dict, Any, Optional


class SessionManager:
    def __init__(self, session_timeout: int = 1800):
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        self.lock = threading.Lock()
        self._start_cleanup()

    def _start_cleanup(self):
        def cleanup():
            while True:
                time.sleep(300)
                self._cleanup_expired()
        threading.Thread(target=cleanup, daemon=True).start()

    def update_session(self, user_id: int, step: Optional[str] = None, **data) -> None:
        with self.lock:
            # Создаем сессию если нужно
            if user_id not in self.sessions:
                self.sessions[user_id] = {
                    'step': None,
                    'data': {},
                    'created_at': time.time(),
                    'updated_at': time.time()
                }
            
            session = self.sessions[user_id]
            
            if step is not None:
                session['step'] = step
            
            if data:
                session['data'].update(data)
            
            session['updated_at'] = time.time()

    def get_user_step(self, user_id: int) -> Optional[str]:
        with self.lock:
            session = self.sessions.get(user_id)
            return session['step'] if session else None

    def get_user_data(self, user_id: int, key: Optional[str] = None) -> Any:
        with self.lock:
            session = self.sessions.get(user_id)
            if not session:
                return None
            return session['data'].get(key) if key else session['data']

    def clear_session(self, user_id: int) -> None:
        with self.lock:
            if user_id in self.sessions:
                del self.sessions[user_id]

    def _cleanup_expired(self):
        with self.lock:
            current_time = time.time()
            expired_users = [
                user_id for user_id, session in self.sessions.items()
                if current_time - session['updated_at'] > self.session_timeout
            ]
            for user_id in expired_users:
                del self.sessions[user_id]
            if expired_users:
                print(f"🧹 Очищено {len(expired_users)} устаревших сессий")