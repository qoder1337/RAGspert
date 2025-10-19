import asyncio
import time
from collections import deque
from functools import wraps


class AsyncRateLimiter:
    _instances = {}  # Dictionary für mehrere Instanzen mit verschiedenen Namen

    @classmethod
    def get_instance(cls, name="default", max_calls=15, period=60):
        """Holt eine benannte Instanz des Rate Limiters oder erstellt eine neue"""
        if name not in cls._instances:
            cls._instances[name] = AsyncRateLimiter(max_calls, period)
        return cls._instances[name]

    def __init__(self, max_calls=15, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Wartet, bis eine Anfrage innerhalb des Rate Limits möglich ist"""
        async with self.lock:
            current_time = time.time()

            # Entferne abgelaufene Zeitstempel
            while self.calls and current_time - self.calls[0] > self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                # Berechne Wartezeit bis der älteste Aufruf abläuft
                sleep_time = self.period - (current_time - self.calls[0])
                print(f"Rate limit erreicht. Warte {sleep_time:.2f} Sekunden...")
                await asyncio.sleep(sleep_time)

                # Nach dem Warten aktualisieren wir die Zeit und die Liste
                current_time = time.time()
                while self.calls and current_time - self.calls[0] > self.period:
                    self.calls.popleft()

            # Füge aktuellen Zeitstempel hinzu
            self.calls.append(current_time)

    def __call__(self, func):
        """Ermöglicht die Verwendung als Decorator"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.acquire()
            return await func(*args, **kwargs)

        return wrapper


# Hilfsfunktion für einfacheren Zugriff
def get_rate_limiter(name="default", max_calls=15, period=60):
    return AsyncRateLimiter.get_instance(name, max_calls, period)


rate_limiter_gemini = get_rate_limiter("gemini rate-limiter", max_calls=30, period=60)
rate_limiter_gemini_embeddings = get_rate_limiter(
    "gemini rate-limiter_embeddings", max_calls=100, period=60
)
