"""
Planificateur quotidien léger (sans dépendance externe, basé sur asyncio).

Déclenche une tâche une fois par jour, le matin, à une minute tirée au hasard
dans une fenêtre [hour:00 ; hour:window_minutes] — ce qui lisse la charge sur
les APIs externes (Google) d'un jour à l'autre.
"""
import os
import asyncio
import random
import datetime

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


class DailyScheduler:
    def __init__(self, callback, hour: int = 8, window_minutes: int = 45,
                 tz: str = "Europe/Paris", name: str = "supervision"):
        self.callback = callback
        self.hour = hour
        self.window_minutes = max(0, window_minutes)
        self.tz_name = tz
        self.name = name
        self._task = None
        self.last_run = None
        self.last_summary = None
        self.next_run = None

    def _tz(self):
        try:
            return ZoneInfo(self.tz_name) if ZoneInfo else None
        except Exception:
            return None

    def _now(self):
        return datetime.datetime.now(self._tz())

    def _compute_next(self) -> datetime.datetime:
        now = self._now()
        today_window_start = now.replace(hour=self.hour, minute=0, second=0, microsecond=0)
        # Une seule exécution par jour : si la fenêtre du matin est déjà passée, on vise demain.
        day = now.date() if now < today_window_start else (now + datetime.timedelta(days=1)).date()
        minute = random.randint(0, self.window_minutes)
        target = datetime.datetime.combine(
            day, datetime.time(self.hour, 0), tzinfo=self._tz()
        ) + datetime.timedelta(minutes=minute)
        return target

    async def _run_loop(self):
        while True:
            self.next_run = self._compute_next()
            delay = max(1.0, (self.next_run - self._now()).total_seconds())
            print(f"[Scheduler:{self.name}] prochaine exécution : {self.next_run.isoformat()} (dans {int(delay)}s)")
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
            try:
                self.last_summary = await self.callback()
                self.last_run = self._now().isoformat()
                print(f"[Scheduler:{self.name}] exécution terminée : {self.last_summary}")
            except Exception as e:
                print(f"[Scheduler:{self.name}] ERREUR : {e}")
            # Évite un re-déclenchement dans la même minute
            await asyncio.sleep(60)

    def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()

    def status(self) -> dict:
        return {
            "enabled": self._task is not None and not self._task.done(),
            "name": self.name,
            "timezone": self.tz_name,
            "window": f"{self.hour:02d}:00 – {self.hour:02d}:{self.window_minutes:02d}",
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run,
            "last_summary": self.last_summary,
        }
