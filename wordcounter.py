# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pynput import keyboard
from pynput.keyboard import Key
import threading
import pandas as pd
from datetime import datetime, timedelta, date
import os
import json
import logging
import re
import shutil
import uuid
import traceback
import platform
import urllib.parse
import webbrowser
from typing import Optional, Dict, Any, List, Tuple, Union, Deque
from collections import deque
import time
from dataclasses import dataclass, field
from pathlib import Path
import sys
from contextlib import contextmanager
import psutil
import subprocess

# Platform capability flags. These drive the dispatch helpers below so the
# rest of the code doesn't have to sprinkle sys.platform checks everywhere.
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

# Windows-only native deps. Guarded so the module can import (and be linted)
# on a Mac or a Linux dev box; anything that actually needs these APIs is
# gated behind IS_WINDOWS at call time.
if IS_WINDOWS:
    import win32gui  # type: ignore[import-not-found]
    import win32process  # type: ignore[import-not-found]
else:
    win32gui = None  # type: ignore[assignment]
    win32process = None  # type: ignore[assignment]

# macOS-only native deps via PyObjC. Imported lazily inside the Mac
# implementations so Windows installs don't need pyobjc at all.
import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from calendar import monthrange
import seaborn as sns


def user_data_dir() -> Path:
    """Directory for config, data, logs (override with WORDCOUNTER_DATA_DIR for dev/tests)."""
    override = os.environ.get("WORDCOUNTER_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "WordCounterPro"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "WordCounterPro"
    return Path.home() / ".wordcounterpro"


def migrate_legacy_data_to_app_dir(app_dir: Path) -> None:
    """If new app dir is empty, copy config/data from current working directory once."""
    app_dir.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd()
    for name in ("config.json", "WordCountData.xlsx"):
        src, dest = cwd / name, app_dir / name
        if src.exists() and not dest.exists():
            try:
                shutil.copy2(src, dest)
            except OSError:
                pass
    cwd_bak, dest_bak = cwd / "backups", app_dir / "backups"
    if cwd_bak.is_dir() and not dest_bak.exists():
        try:
            shutil.copytree(cwd_bak, dest_bak)
        except OSError:
            pass


# Application version. Bump before each friends build.
APP_VERSION = "0.2.0-validate"

# Placeholder feedback email. Replace before distributing builds.
FEEDBACK_EMAIL = "feedback@example.com"


def crashes_dir() -> Path:
    """Directory where crash logs are written."""
    d = user_data_dir() / "crashes"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def _crash_report_text(
    exc_type,
    exc_value,
    exc_tb,
    thread_name: str = "MainThread",
) -> str:
    """Build a crash-report string. Never includes typed text or window titles."""
    try:
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    except Exception:
        tb_text = f"{exc_type!r}: {exc_value!r}\n(traceback formatting failed)"

    header = [
        "WordCounter Crash Report",
        "=" * 40,
        f"Timestamp (local): {datetime.now().isoformat(timespec='seconds')}",
        f"App version:       {APP_VERSION}",
        f"Python:            {sys.version.split()[0]}",
        f"Platform:          {platform.platform()}",
        f"Thread:            {thread_name}",
        "",
        "Privacy notice: this report contains a stack trace and system info only.",
        "No keystrokes, typed words, file contents, or window titles are attached.",
        "",
        "Traceback",
        "-" * 40,
    ]
    return "\n".join(header) + "\n" + tb_text


def write_crash_log(exc_type, exc_value, exc_tb, thread_name: str = "MainThread") -> Optional[Path]:
    """Write a crash log to the crashes directory. Returns the log path or None on failure."""
    try:
        text = _crash_report_text(exc_type, exc_value, exc_tb, thread_name=thread_name)
    except Exception:
        return None
    try:
        d = crashes_dir()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = d / f"crash-{stamp}.log"
        path.write_text(text, encoding="utf-8")
        return path
    except OSError:
        return None


def _handle_uncaught_exception(exc_type, exc_value, exc_tb):
    """Top-level excepthook: write a crash log, then fall through to default handler."""
    try:
        if not issubclass(exc_type, KeyboardInterrupt):
            write_crash_log(exc_type, exc_value, exc_tb)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def _handle_thread_exception(args):
    """threading.excepthook: capture crashes from background threads (Python 3.8+)."""
    try:
        thread_name = getattr(args.thread, "name", "UnknownThread")
        write_crash_log(args.exc_type, args.exc_value, args.exc_traceback, thread_name=thread_name)
    except Exception:
        pass
    try:
        _original_threading_excepthook(args)
    except Exception:
        pass


_original_threading_excepthook = threading.excepthook


def install_crash_handlers() -> None:
    """Install process-wide crash handlers. Safe to call more than once."""
    sys.excepthook = _handle_uncaught_exception
    try:
        threading.excepthook = _handle_thread_exception
    except AttributeError:
        pass


def build_feedback_mailto(body_extra: str = "") -> str:
    """Construct a mailto: URL with app context in the body."""
    lines = [
        "Hi,",
        "",
        "(Your feedback here)",
        "",
        "---",
        f"App version: {APP_VERSION}",
        f"Python:      {sys.version.split()[0]}",
        f"Platform:    {platform.platform()}",
    ]
    if body_extra:
        lines += ["", body_extra]
    body = "\n".join(lines)
    params = {
        "subject": f"WordCounter feedback (v{APP_VERSION})",
        "body": body,
    }
    return "mailto:" + FEEDBACK_EMAIL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


# Add custom exception classes
class WordCounterError(Exception):
    """Base exception for WordCounter application."""
    pass

class ConfigurationError(WordCounterError):
    """Raised when there's an issue with configuration."""
    pass

class DataError(WordCounterError):
    """Raised when there's an issue with data operations."""
    pass

# Enhanced data structures for comprehensive analytics
@dataclass
class WritingSession:
    """Enhanced session data with detailed analytics."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    word_count: int = 0
    duration_minutes: float = 0.0
    wpm: float = 0.0
    productivity_score: float = 0.0
    breaks_taken: int = 0
    total_break_time: float = 0.0
    focus_score: float = 0.0
    application_used: str = ""
    project_name: str = ""
    mood_rating: Optional[int] = None
    energy_level: Optional[int] = None
    notes: str = ""

@dataclass
class WritingGoal:
    """Goal tracking for different time periods."""
    goal_id: str
    goal_type: str  # daily, weekly, monthly, yearly, streak
    target_words: int
    start_date: datetime
    end_date: Optional[datetime] = None
    current_progress: int = 0
    completed: bool = False
    created_date: datetime = field(default_factory=datetime.now)

@dataclass
class Achievement:
    """Achievement system for gamification."""
    achievement_id: str
    name: str
    description: str
    category: str  # speed, consistency, endurance, milestones
    criteria: Dict[str, Any]
    unlocked_date: Optional[datetime] = None
    icon: str = "🏆"

@dataclass
class WritingStreak:
    """Track consecutive days of writing."""
    current_streak: int = 0
    longest_streak: int = 0
    last_writing_date: Optional[datetime] = None
    streak_start_date: Optional[datetime] = None

@dataclass
class WritingInsights:
    """Comprehensive insights and analytics."""
    best_writing_time: str = ""
    most_productive_day: str = ""
    average_session_length: float = 0.0
    consistency_score: float = 0.0
    improvement_rate: float = 0.0
    focus_trend: List[float] = field(default_factory=list)
    productivity_trend: List[float] = field(default_factory=list)
    weekly_patterns: Dict[str, float] = field(default_factory=dict)
    monthly_growth: List[float] = field(default_factory=list)

class AdvancedAnalytics:
    """Comprehensive analytics engine for writing insights."""
    
    def __init__(self):
        self.sessions: List[WritingSession] = []
        self.goals: List[WritingGoal] = []
        self.achievements: List[Achievement] = []
        self.streak = WritingStreak()
        self.insights = WritingInsights()
        
    def add_session(self, session: WritingSession) -> None:
        """Add a new writing session."""
        self.sessions.append(session)
        self._update_streak(session)
        self._check_achievements(session)
        self._update_insights()
        
    def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        """Get comprehensive daily statistics."""
        day_sessions = [s for s in self.sessions if s.start_time.date() == date.date()]
        
        if not day_sessions:
            return {"words_written": 0, "sessions": 0, "total_time": 0, "avg_wpm": 0}
            
        total_words = sum(s.word_count for s in day_sessions)
        total_time = sum(s.duration_minutes for s in day_sessions)
        avg_wpm = sum(s.wpm * s.duration_minutes for s in day_sessions) / total_time if total_time > 0 else 0
        
        return {
            "words_written": total_words,
            "sessions": len(day_sessions),
            "total_time": total_time,
            "avg_wpm": avg_wpm,
            "focus_score": sum(s.focus_score for s in day_sessions) / len(day_sessions),
            "productivity_score": sum(s.productivity_score for s in day_sessions) / len(day_sessions)
        }
        
    def get_weekly_stats(self, start_date: datetime) -> Dict[str, Any]:
        """Get comprehensive weekly statistics."""
        end_date = start_date + timedelta(days=7)
        week_sessions = [s for s in self.sessions 
                        if start_date <= s.start_time < end_date]
        
        if not week_sessions:
            return {"total_words": 0, "sessions": 0, "avg_daily_words": 0}
            
        total_words = sum(s.word_count for s in week_sessions)
        total_sessions = len(week_sessions)
        
        # Daily breakdown
        daily_words = {}
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            daily_words[day_date.strftime('%A')] = self.get_daily_stats(day_date)["words_written"]
        
        return {
            "total_words": total_words,
            "sessions": total_sessions,
            "avg_daily_words": total_words / 7,
            "daily_breakdown": daily_words,
            "consistency_score": self._calculate_consistency(daily_words.values()),
            "best_day": max(daily_words.items(), key=lambda x: x[1])[0]
        }
        
    def get_monthly_stats(self, year: int, month: int) -> Dict[str, Any]:
        """Get comprehensive monthly statistics."""
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
        
        month_sessions = [s for s in self.sessions 
                         if start_date <= s.start_time <= end_date]
        
        if not month_sessions:
            return {"total_words": 0, "sessions": 0, "avg_daily_words": 0}
            
        total_words = sum(s.word_count for s in month_sessions)
        total_sessions = len(month_sessions)
        days_in_month = monthrange(year, month)[1]
        
        # Weekly breakdown
        weekly_words = []
        for week_start in range(0, days_in_month, 7):
            week_date = start_date + timedelta(days=week_start)
            week_stats = self.get_weekly_stats(week_date)
            weekly_words.append(week_stats["total_words"])
        
        return {
            "total_words": total_words,
            "sessions": total_sessions,
            "avg_daily_words": total_words / days_in_month,
            "weekly_breakdown": weekly_words,
            "growth_rate": self._calculate_growth_rate(weekly_words),
            "most_productive_week": weekly_words.index(max(weekly_words)) + 1 if weekly_words else 0
        }
        
    def get_writing_insights(self) -> Dict[str, Any]:
        """Generate comprehensive writing insights."""
        if not self.sessions:
            return {}
            
        # Best writing time analysis
        hour_productivity = {}
        for session in self.sessions:
            hour = session.start_time.hour
            if hour not in hour_productivity:
                hour_productivity[hour] = []
            hour_productivity[hour].append(session.wpm)
        
        best_hour = max(hour_productivity.items(), key=lambda x: np.mean(x[1]))[0] if hour_productivity else 0
        
        # Day of week analysis
        day_productivity = {}
        for session in self.sessions:
            day = session.start_time.strftime('%A')
            if day not in day_productivity:
                day_productivity[day] = []
            day_productivity[day].append(session.word_count)
        
        best_day = max(day_productivity.items(), key=lambda x: np.mean(x[1]))[0] if day_productivity else "Unknown"
        
        # Consistency analysis
        recent_sessions = [s for s in self.sessions 
                          if s.start_time > datetime.now() - timedelta(days=30)]
        consistency_score = self._calculate_consistency([s.word_count for s in recent_sessions])
        
        # Improvement analysis
        if len(self.sessions) >= 10:
            recent_wpm = [s.wpm for s in self.sessions[-10:]]
            older_wpm = [s.wpm for s in self.sessions[-20:-10]]
            improvement_rate = (np.mean(recent_wpm) - np.mean(older_wpm)) / np.mean(older_wpm) * 100
        else:
            improvement_rate = 0.0
        
        return {
            "best_writing_time": f"{best_hour:02d}:00",
            "most_productive_day": best_day,
            "consistency_score": consistency_score,
            "improvement_rate": improvement_rate,
            "current_streak": self.streak.current_streak,
            "longest_streak": self.streak.longest_streak,
            "total_sessions": len(self.sessions),
            "total_words_written": sum(s.word_count for s in self.sessions),
            "average_session_length": np.mean([s.duration_minutes for s in self.sessions]),
            "average_wpm": np.mean([s.wpm for s in self.sessions]),
            "focus_trend": self._calculate_focus_trend(),
            "productivity_trend": self._calculate_productivity_trend()
        }
        
    def _update_streak(self, session: WritingSession) -> None:
        """Update writing streak information."""
        today = session.start_time.date()
        
        if self.streak.last_writing_date is None:
            self.streak.current_streak = 1
            self.streak.longest_streak = 1
            self.streak.streak_start_date = session.start_time
        elif today == self.streak.last_writing_date:
            # Same day, don't update streak
            pass
        elif today == self.streak.last_writing_date + timedelta(days=1):
            # Consecutive day
            self.streak.current_streak += 1
            self.streak.longest_streak = max(self.streak.longest_streak, self.streak.current_streak)
        else:
            # Streak broken
            self.streak.current_streak = 1
            self.streak.streak_start_date = session.start_time
            
        self.streak.last_writing_date = today
        
    def _check_achievements(self, session: WritingSession) -> List[Achievement]:
        """Check for newly unlocked achievements."""
        newly_unlocked = []
        
        # Speed achievements
        if session.wpm >= 100 and not self._has_achievement("speed_demon"):
            achievement = Achievement(
                achievement_id="speed_demon",
                name="Speed Demon",
                description="Achieved 100+ WPM in a session",
                category="speed",
                criteria={"wpm_threshold": 100}
            )
            achievement.unlocked_date = datetime.now()
            self.achievements.append(achievement)
            newly_unlocked.append(achievement)
            
        # Consistency achievements
        if self.streak.current_streak >= 7 and not self._has_achievement("week_warrior"):
            achievement = Achievement(
                achievement_id="week_warrior",
                name="Week Warrior",
                description="7-day writing streak",
                category="consistency",
                criteria={"streak_threshold": 7}
            )
            achievement.unlocked_date = datetime.now()
            self.achievements.append(achievement)
            newly_unlocked.append(achievement)
            
        # Endurance achievements
        if session.duration_minutes >= 120 and not self._has_achievement("marathon_writer"):
            achievement = Achievement(
                achievement_id="marathon_writer",
                name="Marathon Writer",
                description="2+ hour writing session",
                category="endurance",
                criteria={"duration_threshold": 120}
            )
            achievement.unlocked_date = datetime.now()
            self.achievements.append(achievement)
            newly_unlocked.append(achievement)
            
        # Milestone achievements
        total_words = sum(s.word_count for s in self.sessions)
        if total_words >= 10000 and not self._has_achievement("word_master"):
            achievement = Achievement(
                achievement_id="word_master",
                name="Word Master",
                description="10,000 total words written",
                category="milestones",
                criteria={"word_threshold": 10000}
            )
            achievement.unlocked_date = datetime.now()
            self.achievements.append(achievement)
            newly_unlocked.append(achievement)
            
        return newly_unlocked
        
    def _has_achievement(self, achievement_id: str) -> bool:
        """Check if user already has a specific achievement."""
        return any(a.achievement_id == achievement_id for a in self.achievements)
        
    def _calculate_consistency(self, values: List[float]) -> float:
        """Calculate consistency score based on variance."""
        if len(values) < 2:
            return 1.0
        mean_val = np.mean(values)
        if mean_val == 0:
            return 0.0
        variance = np.var(values)
        return max(0, 1 - (variance / (mean_val ** 2)))
        
    def _calculate_growth_rate(self, weekly_values: List[float]) -> float:
        """Calculate growth rate over time."""
        if len(weekly_values) < 2:
            return 0.0
        return ((weekly_values[-1] - weekly_values[0]) / weekly_values[0]) * 100 if weekly_values[0] > 0 else 0
        
    def _calculate_focus_trend(self) -> List[float]:
        """Calculate focus score trend over recent sessions."""
        recent_sessions = self.sessions[-20:] if len(self.sessions) >= 20 else self.sessions
        return [s.focus_score for s in recent_sessions]
        
    def _calculate_productivity_trend(self) -> List[float]:
        """Calculate productivity score trend over recent sessions."""
        recent_sessions = self.sessions[-20:] if len(self.sessions) >= 20 else self.sessions
        return [s.productivity_score for s in recent_sessions]
        
    def _update_insights(self) -> None:
        """Update comprehensive insights."""
        insights = self.get_writing_insights()
        self.insights.best_writing_time = insights.get("best_writing_time", "")
        self.insights.most_productive_day = insights.get("most_productive_day", "")
        self.insights.consistency_score = insights.get("consistency_score", 0.0)
        self.insights.improvement_rate = insights.get("improvement_rate", 0.0)
        self.insights.focus_trend = insights.get("focus_trend", [])
        self.insights.productivity_trend = insights.get("productivity_trend", [])

    def bulk_load_sessions(self, sessions: List[WritingSession]) -> None:
        """Load persisted sessions without per-row achievement checks (used at startup)."""
        # Dedupe by session_id so xlsx rows + in-memory adds do not double-count after restart
        by_id: Dict[str, WritingSession] = {}
        for s in sorted(sessions, key=lambda x: x.start_time):
            by_id[s.session_id] = s
        self.sessions = list(by_id.values())
        self.achievements.clear()
        self.streak = WritingStreak()
        for s in self.sessions:
            self._update_streak(s)
        self._update_insights()

class GoalManager:
    """Manages writing goals and progress tracking."""
    
    def __init__(self, analytics: Optional[AdvancedAnalytics] = None):
        self.goals: List[WritingGoal] = []
        self.analytics = analytics if analytics is not None else AdvancedAnalytics()
        
    def create_goal(self, goal_type: str, target_words: int, 
                   start_date: datetime, end_date: Optional[datetime] = None) -> WritingGoal:
        """Create a new writing goal."""
        goal = WritingGoal(
            goal_id=f"goal_{int(time.time())}",
            goal_type=goal_type,
            target_words=target_words,
            start_date=start_date,
            end_date=end_date
        )
        self.goals.append(goal)
        return goal
        
    def update_goal_progress(self, words_written: int) -> List[WritingGoal]:
        """Update progress for all active goals."""
        completed_goals = []
        
        for goal in self.goals:
            if not goal.completed and (goal.end_date is None or datetime.now() <= goal.end_date):
                goal.current_progress += words_written
                
                if goal.current_progress >= goal.target_words:
                    goal.completed = True
                    goal.end_date = datetime.now()
                    completed_goals.append(goal)
                    
        return completed_goals
        
    def get_active_goals(self) -> List[WritingGoal]:
        """Get all active (non-completed) goals."""
        return [g for g in self.goals if not g.completed]
        
    def get_goal_progress(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress for a specific goal."""
        goal = next((g for g in self.goals if g.goal_id == goal_id), None)
        if not goal:
            return None
            
        progress_percentage = (goal.current_progress / goal.target_words) * 100
        days_remaining = None
        if goal.end_date:
            days_remaining = (goal.end_date - datetime.now()).days
            
        return {
            "goal": goal,
            "progress_percentage": progress_percentage,
            "words_remaining": goal.target_words - goal.current_progress,
            "days_remaining": days_remaining,
            "on_track": self._is_goal_on_track(goal)
        }
        
    def _is_goal_on_track(self, goal: WritingGoal) -> bool:
        """Check if a goal is on track to be completed on time."""
        if goal.end_date is None:
            return True
            
        elapsed_days = (datetime.now() - goal.start_date).days
        total_days = (goal.end_date - goal.start_date).days
        
        if total_days <= 0:
            return goal.current_progress >= goal.target_words
            
        expected_progress = (elapsed_days / total_days) * goal.target_words
        return goal.current_progress >= expected_progress

# ----------------------------------------------------------------------------
# Platform dispatch helpers
# ----------------------------------------------------------------------------
#
# Everything below is a thin cross-platform veneer so the rest of the app can
# ask questions like "which app is focused?" or "is the app set to launch at
# login?" without caring whether we're on Windows or macOS.


def _foreground_info_windows() -> Tuple[str, str, Any]:
    """Windows: return (process_name_lower, window_title_lower, hwnd_cache_key)."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return "", "", None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        window_title = win32gui.GetWindowText(hwnd) or ""
        try:
            process_name = psutil.Process(pid).name().lower()
        except Exception:
            process_name = ""
        return process_name, window_title.lower(), hwnd
    except Exception:
        return "", "", None


def _foreground_info_macos() -> Tuple[str, str, Any]:
    """macOS: return (app_name_lower, "", bundle_id_cache_key) via NSWorkspace.

    We return an empty string for the window title on Mac because NSWorkspace
    only reports the frontmost *application*, not its frontmost window title.
    The allowlist matches on app name only, so this is fine.
    """
    try:
        from AppKit import NSWorkspace  # type: ignore[import-not-found]
    except Exception:
        return "", "", None
    try:
        ws = NSWorkspace.sharedWorkspace()
        app = ws.frontmostApplication() if ws is not None else None
        if app is None:
            return "", "", None
        name = (app.localizedName() or "").lower()
        bundle_id = app.bundleIdentifier() or ""
        return name, "", bundle_id or name
    except Exception:
        return "", "", None


def get_foreground_info() -> Tuple[str, str, Any]:
    """Return (focus_app_name_lower, window_title_lower, cache_key).

    The returned ``cache_key`` is an opaque, equality-comparable value that
    identifies the current focused app/window. Callers can cache per-focus
    computations against it cheaply.
    """
    if IS_WINDOWS:
        return _foreground_info_windows()
    if IS_MACOS:
        return _foreground_info_macos()
    return "", "", None


def open_in_file_manager(path: Path) -> bool:
    """Open a directory in the OS file manager. Returns True on success."""
    try:
        if IS_WINDOWS:
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        if IS_MACOS:
            subprocess.run(["open", str(path)], check=False)
            return True
        webbrowser.open(path.as_uri())
        return True
    except Exception as e:
        logging.warning(f"open_in_file_manager failed for {path}: {e}")
        return False


class AppFocusManager:
    """Tracks the focused application and enforces the writing-app allowlist.

    The app is *not* a general keystroke logger: the keyboard listener is only
    instantiated while an allowlisted writing app is the focused foreground
    window. This class is the authority on "is the user currently in a
    writing app?" and persists the allowlist via the shared Config.
    """

    def __init__(self, config: Optional["Config"] = None):
        self._config = config
        initial = config.get("allowed_apps", []) if config is not None else []
        if not initial:
            initial = list(Config.DEFAULT_ALLOWED_APPS) if hasattr(Config, "DEFAULT_ALLOWED_APPS") else []
        self.allowed_apps: set = {a.lower() for a in initial}

        self.current_app: Optional[str] = None
        self.current_window_title: Optional[str] = None
        self._unknown_context_warned = False
        # Hot path (hit on every keystroke): cache the writing-context decision
        # against whatever opaque key the platform backend hands us (hwnd on
        # Windows, bundle id on macOS).
        self._ctx_key: Any = None
        self._ctx_mono: float = 0.0
        self._ctx_is_writing: bool = False

    def get_active_window_info(self) -> Tuple[str, str]:
        """Return (focused app name, window title) as lowercased strings."""
        name, title, _ = get_foreground_info()
        return name, title

    def is_writing_context(self) -> bool:
        """Return True iff the focused foreground window is an allowlisted writing app."""
        try:
            process_name, _, cache_key = get_foreground_info()
            now = time.monotonic()
            if cache_key is not None and cache_key == self._ctx_key and (now - self._ctx_mono) < 1.0:
                return self._ctx_is_writing

            if not process_name:
                if not self._unknown_context_warned:
                    logging.warning("Unable to determine active window context; treating as non-writing for safety.")
                    self._unknown_context_warned = True
                is_writing = False
            else:
                is_writing = process_name in self.allowed_apps

            self._ctx_key = cache_key
            self._ctx_mono = now
            self._ctx_is_writing = is_writing
            return is_writing

        except Exception:
            return False

    def update_context(self) -> None:
        """Update current application context (for display / debug)."""
        self.current_app, self.current_window_title = self.get_active_window_info()

    def _persist(self) -> None:
        if self._config is None:
            return
        try:
            self._config.set("allowed_apps", sorted(self.allowed_apps))
            self._config.save_config()
        except Exception as e:
            logging.warning(f"Failed to persist allowed_apps: {e}")

    def _invalidate_cache(self) -> None:
        self._ctx_key = None
        self._ctx_mono = 0.0
        self._ctx_is_writing = False

    def add_allowed_app(self, app_name: str) -> None:
        """Add an application to the writing-app allowlist."""
        self.allowed_apps.add(app_name.lower())
        self._invalidate_cache()
        self._persist()

    def remove_allowed_app(self, app_name: str) -> None:
        """Remove an application from the writing-app allowlist."""
        self.allowed_apps.discard(app_name.lower())
        self._invalidate_cache()
        self._persist()

    def get_allowed_apps(self) -> set:
        """Get the current writing-app allowlist."""
        return self.allowed_apps.copy()

    def set_allowed_apps(self, app_names) -> None:
        """Replace the entire allowlist (used by onboarding / bulk edits)."""
        self.allowed_apps = {a.lower() for a in app_names}
        self._invalidate_cache()
        self._persist()


RUN_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_REGISTRY_VALUE_NAME = "WordCounterPro"


# Human-readable display names for the apps the user is likely to see.
# On Windows the allowlist is stored as lowercase *.exe process names; on macOS
# it's stored as the lowercased NSRunningApplication.localizedName. Either way,
# this map (and the fallback in friendly_app_name) only affects what gets
# rendered in the UI.
_FRIENDLY_APP_NAMES_WINDOWS: Dict[str, str] = {
    "winword.exe": "Microsoft Word",
    "obsidian.exe": "Obsidian",
    "evernote.exe": "Evernote",
    "scrivener.exe": "Scrivener",
    "notepad.exe": "Notepad",
    "notepad++.exe": "Notepad++",
    "sublime_text.exe": "Sublime Text",
    "typora.exe": "Typora",
    "wordpad.exe": "WordPad",
    "onenote.exe": "OneNote",
    "joplin.exe": "Joplin",
    "logseq.exe": "Logseq",
    "zettlr.exe": "Zettlr",
    "ia writer.exe": "iA Writer",
    "code.exe": "VS Code",
    "cursor.exe": "Cursor",
}

# On macOS, localizedName is already the human-readable label ("Obsidian",
# "Microsoft Word"). This map is just a title-case fix-up for the ones whose
# lowercased localizedName loses information (e.g. "ia writer" -> "iA Writer").
_FRIENDLY_APP_NAMES_MACOS: Dict[str, str] = {
    "microsoft word": "Microsoft Word",
    "obsidian": "Obsidian",
    "evernote": "Evernote",
    "scrivener": "Scrivener",
    "ulysses": "Ulysses",
    "ia writer": "iA Writer",
    "notes": "Notes",
    "textedit": "TextEdit",
    "bbedit": "BBEdit",
    "sublime text": "Sublime Text",
    "typora": "Typora",
    "notion": "Notion",
    "bear": "Bear",
    "logseq": "Logseq",
    "visual studio code": "Visual Studio Code",
    "cursor": "Cursor",
}

FRIENDLY_APP_NAMES: Dict[str, str] = (
    _FRIENDLY_APP_NAMES_MACOS if IS_MACOS else _FRIENDLY_APP_NAMES_WINDOWS
)


def friendly_app_name(process_name: str) -> str:
    """Return a human-readable display name for the focused app.

    On Windows the input is a lowercased ``*.exe`` name; on macOS it's the
    lowercased ``localizedName``. Known apps come from ``FRIENDLY_APP_NAMES``;
    unknown apps fall back to a cleaned-up title-cased form.
    """
    if not process_name:
        return ""
    lower = process_name.lower().strip()
    if lower in FRIENDLY_APP_NAMES:
        return FRIENDLY_APP_NAMES[lower]
    base = lower[:-4] if lower.endswith(".exe") else lower
    base = base.replace("_", " ").replace("-", " ")
    return base.title() if base else process_name


def _build_startup_command() -> str:
    """Build the command Windows should run at login to launch this app."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script = Path(__file__).resolve()
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    interpreter = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{interpreter}" "{script}"'


def _set_launch_on_startup_windows(enable: bool) -> bool:
    """Windows: add/remove the HKCU Run registry entry for auto-launch."""
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enable:
                winreg.SetValueEx(k, RUN_REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, _build_startup_command())
            else:
                try:
                    winreg.DeleteValue(k, RUN_REGISTRY_VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        logging.warning(f"set_launch_on_startup failed: {e}")
        return False


def _is_launch_on_startup_windows() -> bool:
    """Windows: return True iff the HKCU Run registry entry is present."""
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REGISTRY_KEY, 0, winreg.KEY_READ) as k:
            try:
                winreg.QueryValueEx(k, RUN_REGISTRY_VALUE_NAME)
                return True
            except FileNotFoundError:
                return False
    except Exception:
        return False


def set_launch_on_startup(enable: bool) -> bool:
    """Platform-dispatched toggle for 'launch this app on login'."""
    if IS_WINDOWS:
        return _set_launch_on_startup_windows(enable)
    if IS_MACOS:
        return _set_launch_on_startup_macos(enable)
    return False


def is_launch_on_startup() -> bool:
    """Platform-dispatched query for the current auto-launch state."""
    if IS_WINDOWS:
        return _is_launch_on_startup_windows()
    if IS_MACOS:
        return _is_launch_on_startup_macos()
    return False


class _WindowsFocusWatcher:
    """Watches foreground-window changes via Win32 SetWinEventHook.

    Runs a private Windows message loop in a daemon thread. On each
    EVENT_SYSTEM_FOREGROUND event, resolves the focused process name and
    schedules ``on_focus_change(process_name)`` back on the Tk main thread
    via ``root.after``. Used to start/stop the pynput keyboard listener so
    it's only instantiated while an allowlisted writing app is focused.
    """

    EVENT_SYSTEM_FOREGROUND = 0x0003
    WINEVENT_OUTOFCONTEXT = 0x0000
    WM_QUIT = 0x0012

    def __init__(self, root: tk.Tk, on_focus_change):
        self._root = root
        self._on_focus_change = on_focus_change
        self._thread: Optional[threading.Thread] = None
        self._thread_id: int = 0
        self._hook_id = None
        self._proc = None  # keep a ref to the ctypes callback so it isn't GC'd
        self._started = threading.Event()

        import ctypes
        from ctypes import wintypes
        self._ctypes = ctypes
        self._wintypes = wintypes
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="FocusWatcher", daemon=True)
        self._thread.start()
        self._started.wait(timeout=2.0)

    def stop(self) -> None:
        try:
            if self._thread_id:
                self._user32.PostThreadMessageW(self._thread_id, self.WM_QUIT, 0, 0)
            if self._thread is not None:
                self._thread.join(timeout=2.0)
        except Exception as e:
            logging.warning(f"FocusWatcher.stop error: {e}")
        finally:
            self._thread = None

    def _resolve_process_name(self, hwnd) -> str:
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid).name().lower()
        except Exception:
            return ""

    def _schedule(self, process_name: str) -> None:
        try:
            self._root.after(0, lambda p=process_name: self._on_focus_change(p))
        except Exception:
            pass

    def _run(self) -> None:
        ctypes = self._ctypes
        wintypes = self._wintypes

        WinEventProcType = ctypes.WINFUNCTYPE(
            None,
            ctypes.c_void_p,   # hWinEventHook (HWINEVENTHOOK)
            wintypes.DWORD,    # event
            wintypes.HWND,     # hwnd
            wintypes.LONG,     # idObject
            wintypes.LONG,     # idChild
            wintypes.DWORD,    # dwEventThread
            wintypes.DWORD,    # dwmsEventTime
        )

        def _callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
            try:
                process_name = self._resolve_process_name(hwnd)
                self._schedule(process_name)
            except Exception:
                pass

        self._proc = WinEventProcType(_callback)
        self._thread_id = self._kernel32.GetCurrentThreadId()

        self._user32.SetWinEventHook.restype = ctypes.c_void_p
        self._user32.SetWinEventHook.argtypes = [
            wintypes.DWORD, wintypes.DWORD,
            wintypes.HMODULE, WinEventProcType,
            wintypes.DWORD, wintypes.DWORD,
            wintypes.DWORD,
        ]
        self._hook_id = self._user32.SetWinEventHook(
            self.EVENT_SYSTEM_FOREGROUND,
            self.EVENT_SYSTEM_FOREGROUND,
            None,
            self._proc,
            0,
            0,
            self.WINEVENT_OUTOFCONTEXT,
        )
        if not self._hook_id:
            logging.error("SetWinEventHook failed; focus tracking disabled.")
            self._started.set()
            return

        self._started.set()
        msg = wintypes.MSG()
        try:
            while True:
                ret = self._user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
                if ret == 0 or ret == -1:
                    break
                self._user32.TranslateMessage(ctypes.byref(msg))
                self._user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            try:
                self._user32.UnhookWinEvent.argtypes = [ctypes.c_void_p]
                self._user32.UnhookWinEvent(self._hook_id)
            except Exception:
                pass
            self._hook_id = None
            self._proc = None


class _NullFocusWatcher:
    """Fallback watcher for unsupported platforms: does nothing, safely."""

    def __init__(self, root: tk.Tk, on_focus_change):
        self._root = root
        self._on_focus_change = on_focus_change

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


class _MacFocusWatcher:
    """Watches focused-app changes on macOS via NSWorkspace notifications.

    Subscribes to ``NSWorkspaceDidActivateApplicationNotification`` on the
    shared NSWorkspace notification center. Each notification fires the
    callback ``on_focus_change(localizedName_lowercased)`` back on the Tk
    main thread via ``root.after``.

    No polling loop: the observer is driven by Cocoa's run loop, and NSWorkspace
    guarantees notifications on app activation (including the initial startup
    activation of the app the user was in when we launched).
    """

    def __init__(self, root: tk.Tk, on_focus_change):
        self._root = root
        self._on_focus_change = on_focus_change
        self._observer = None
        self._center = None

    def start(self) -> None:
        if self._observer is not None:
            return
        try:
            import objc  # type: ignore[import-not-found]
            from AppKit import NSWorkspace  # type: ignore[import-not-found]
            from Foundation import NSObject  # type: ignore[import-not-found]
        except Exception as e:
            logging.error(f"FocusWatcher (mac): PyObjC not available: {e}")
            return

        outer = self

        class _Observer(NSObject):  # type: ignore[misc]
            def appActivated_(self, notification):
                try:
                    info = notification.userInfo() if notification is not None else None
                    app = info.get("NSWorkspaceApplicationKey") if info is not None else None
                    name = ""
                    if app is not None:
                        try:
                            name = (app.localizedName() or "").lower()
                        except Exception:
                            name = ""
                    outer._schedule(name)
                except Exception:
                    pass

        try:
            ws = NSWorkspace.sharedWorkspace()
            self._center = ws.notificationCenter()
            self._observer = _Observer.alloc().init()
            self._center.addObserver_selector_name_object_(
                self._observer,
                objc.selector(self._observer.appActivated_, signature=b"v@:@"),
                "NSWorkspaceDidActivateApplicationNotification",
                None,
            )
            # Also immediately dispatch the current frontmost app so callers
            # aren't blind until the user next switches apps.
            try:
                current = ws.frontmostApplication()
                if current is not None:
                    self._schedule((current.localizedName() or "").lower())
            except Exception:
                pass
        except Exception as e:
            logging.error(f"FocusWatcher (mac) start failed: {e}")
            self._observer = None
            self._center = None

    def stop(self) -> None:
        try:
            if self._center is not None and self._observer is not None:
                self._center.removeObserver_(self._observer)
        except Exception as e:
            logging.warning(f"FocusWatcher (mac) stop error: {e}")
        finally:
            self._observer = None
            self._center = None

    def _schedule(self, process_name: str) -> None:
        try:
            self._root.after(0, lambda p=process_name: self._on_focus_change(p))
        except Exception:
            pass


class _MacLaunchAgent:
    """Manages a per-user LaunchAgent plist for 'launch at login' on macOS.

    We write the plist to ``~/Library/LaunchAgents/com.wordcounterpro.agent.plist``
    and load it with ``launchctl``. The ProgramArguments target is the
    executable inside the .app bundle when running a frozen build, or the
    current python + script when running from source.
    """

    LABEL = "com.wordcounterpro.agent"

    def __init__(self) -> None:
        home = Path.home()
        self.plist_path = home / "Library" / "LaunchAgents" / f"{self.LABEL}.plist"

    def _program_arguments(self) -> List[str]:
        if getattr(sys, "frozen", False):
            # PyInstaller .app bundle: sys.executable points at
            # WordCounterPro.app/Contents/MacOS/WordCounterPro
            return [str(Path(sys.executable).resolve())]
        script = str(Path(__file__).resolve())
        return [sys.executable, script]

    def _plist_body(self) -> str:
        args_xml = "\n".join(
            f"        <string>{a}</string>" for a in self._program_arguments()
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            '<dict>\n'
            f'    <key>Label</key>\n    <string>{self.LABEL}</string>\n'
            '    <key>ProgramArguments</key>\n    <array>\n'
            f'{args_xml}\n    </array>\n'
            '    <key>RunAtLoad</key>\n    <true/>\n'
            '    <key>KeepAlive</key>\n    <false/>\n'
            '    <key>ProcessType</key>\n    <string>Interactive</string>\n'
            '</dict>\n'
            '</plist>\n'
        )

    def set_enabled(self, enable: bool) -> bool:
        try:
            if enable:
                self.plist_path.parent.mkdir(parents=True, exist_ok=True)
                self.plist_path.write_text(self._plist_body(), encoding="utf-8")
                subprocess.run(
                    ["launchctl", "unload", str(self.plist_path)],
                    check=False,
                    capture_output=True,
                )
                result = subprocess.run(
                    ["launchctl", "load", "-w", str(self.plist_path)],
                    check=False,
                    capture_output=True,
                )
                return result.returncode == 0
            else:
                if self.plist_path.exists():
                    subprocess.run(
                        ["launchctl", "unload", "-w", str(self.plist_path)],
                        check=False,
                        capture_output=True,
                    )
                    try:
                        self.plist_path.unlink()
                    except FileNotFoundError:
                        pass
                return True
        except Exception as e:
            logging.warning(f"_MacLaunchAgent.set_enabled({enable}) failed: {e}")
            return False

    def is_enabled(self) -> bool:
        return self.plist_path.is_file()


class FocusWatcher:
    """Platform-dispatching facade for the real focus watcher.

    Callers construct ``FocusWatcher(root, on_focus_change)`` and call
    ``.start()`` / ``.stop()``; the right platform backend is chosen here.
    """

    def __new__(cls, root: tk.Tk, on_focus_change):
        if IS_WINDOWS:
            return _WindowsFocusWatcher(root, on_focus_change)
        if IS_MACOS:
            return _MacFocusWatcher(root, on_focus_change)
        return _NullFocusWatcher(root, on_focus_change)


# ----------------------------------------------------------------------------
# macOS backends
# ----------------------------------------------------------------------------
#
# Stubs below are real on Darwin (filled in by later sections of this module)
# and no-ops on other platforms. We keep the function names stable so the
# dispatch helpers above never have to guard imports.

def _set_launch_on_startup_macos(enable: bool) -> bool:
    """macOS: add/remove the per-user LaunchAgent plist. See _MacLaunchAgent."""
    return _MacLaunchAgent().set_enabled(enable) if IS_MACOS else False


def _is_launch_on_startup_macos() -> bool:
    """macOS: True iff our LaunchAgent plist is installed."""
    return _MacLaunchAgent().is_enabled() if IS_MACOS else False


# macOS permission helpers. These are silent probes used by the onboarding
# wizard and the 'Check Permissions' menu command. None == unknown (e.g.
# PyObjC missing). They do NOT trigger macOS's one-time permission prompt.

def mac_accessibility_granted() -> Optional[bool]:
    """True/False for current Accessibility grant; None if we couldn't check."""
    if not IS_MACOS:
        return None
    try:
        from ApplicationServices import AXIsProcessTrusted  # type: ignore[import-not-found]
        return bool(AXIsProcessTrusted())
    except Exception:
        return None


def mac_input_monitoring_granted() -> Optional[bool]:
    """True/False for current Input Monitoring grant; None if we couldn't check."""
    if not IS_MACOS:
        return None
    try:
        from Quartz import CGPreflightListenEventAccess  # type: ignore[import-not-found]
        return bool(CGPreflightListenEventAccess())
    except Exception:
        return None


def open_mac_privacy_pane(pane: str) -> bool:
    """Open a specific pane of System Settings > Privacy & Security.

    ``pane`` is one of ``accessibility`` or ``input_monitoring``. Returns
    True if the URL scheme was dispatched, False otherwise.
    """
    urls = {
        "accessibility": "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        "input_monitoring": "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
    }
    url = urls.get(pane)
    if not url:
        return False
    try:
        subprocess.run(["open", url], check=False)
        return True
    except Exception as e:
        logging.warning(f"open_mac_privacy_pane({pane}) failed: {e}")
        return False


@dataclass
class SessionData:
    """Data class for session information."""
    word_count: int = 0
    start_time: Optional[datetime] = None
    duration: int = 0
    wpm: float = 0.0
    session_id: str = ""
    words_per_minute_history: Deque[float] = field(default_factory=deque)
    
    def reset(self) -> None:
        """Reset session data."""
        self.word_count = 0
        self.start_time = None
        self.duration = 0
        self.wpm = 0.0
        self.session_id = ""
        self.words_per_minute_history.clear()

@dataclass
class AppState:
    """Data class for application state."""
    recording: bool = False
    paused: bool = False
    auto_save_enabled: bool = True
    notifications_enabled: bool = True

class KeyboardShortcuts:
    """Manage keyboard shortcuts for the application."""
    
    def __init__(self, app):
        self.app = app
        self.shortcuts = {
            '<Control-r>': self.app.start_recording,
            '<Control-p>': self.app.toggle_pause,
            '<Control-s>': self.app.stop_recording,
            '<Control-e>': self.app.export_data,
            '<Control-q>': self.app.on_close,
            '<F1>': self.app.show_about,
        }
    
    def bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts to the main window."""
        for key, command in self.shortcuts.items():
            self.app.root.bind(key, lambda e, cmd=command: cmd())
    
    def show_shortcuts_help(self) -> None:
        """Show keyboard shortcuts help dialog."""
        shortcuts_text = """
Keyboard Shortcuts:
• Ctrl+R - Start/Resume Recording
• Ctrl+P - Pause Recording
• Ctrl+S - Stop Recording
• Ctrl+E - Export Data
• Ctrl+Q - Quit Application
• F1 - Show About
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text.strip())


class Config:
    """Configuration management for the application."""

    # Default writing-app allowlist, keyed per platform.
    # Windows matches on lowercase process exe names; macOS matches on
    # lowercase NSRunningApplication.localizedName.
    _DEFAULT_ALLOWED_APPS_WINDOWS = [
        "winword.exe",       # Microsoft Word
        "obsidian.exe",      # Obsidian
        "evernote.exe",      # Evernote
        "scrivener.exe",     # Scrivener
        "notepad.exe",       # Windows Notepad
        "notepad++.exe",     # Notepad++
        "sublime_text.exe",  # Sublime Text
        "typora.exe",        # Typora
        "wordpad.exe",       # WordPad
        "onenote.exe",       # OneNote (desktop)
    ]
    _DEFAULT_ALLOWED_APPS_MACOS = [
        "microsoft word",
        "obsidian",
        "evernote",
        "scrivener",
        "ulysses",
        "ia writer",
        "notes",
        "textedit",
        "bbedit",
        "sublime text",
        "typora",
        "bear",
        "logseq",
    ]
    DEFAULT_ALLOWED_APPS = (
        _DEFAULT_ALLOWED_APPS_MACOS if IS_MACOS else _DEFAULT_ALLOWED_APPS_WINDOWS
    )

    DEFAULT_CONFIG = {
        "auto_save_interval": 300,  # seconds
        "data_flush_interval": 60,  # seconds
        "daily_goal": 1000,
        # Windows-native ttk theme; falls back to 'clam' if unavailable.
        "theme": "vista",
        "window_geometry": "760x560",
        "show_notifications": True,
        "backup_enabled": True,
        "max_backup_files": 5,
        "min_word_length": 2,
        "wpm_history_size": 10,
        # Writing-app allowlist. The keyboard listener only runs while one
        # of these process names is the focused foreground window.
        "allowed_apps": list(DEFAULT_ALLOWED_APPS),
        # First-run wizard gate. False => show wizard on next launch.
        "onboarding_completed": False,
        # Reconciled against HKCU\...\Run on each startup.
        "launch_on_startup": False,
    }
    
    def __init__(self, config_file: Union[str, Path] = "config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self._validate_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults, ensuring all required keys exist
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    return config
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Error loading config file: {e}. Using defaults.")
        except Exception as e:
            logging.error(f"Unexpected error loading config: {e}")
        
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if enabled
            if self.config.get("backup_enabled", True) and self.config_file.exists():
                self._create_backup()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                
        except IOError as e:
            logging.error(f"Error saving config: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
        except Exception as e:
            logging.error(f"Unexpected error saving config: {e}")
            raise ConfigurationError(f"Unexpected error saving configuration: {e}")
    
    def _create_backup(self) -> None:
        """Create a backup of the current config file."""
        try:
            backup_dir = self.config_file.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"config_backup_{timestamp}.json"
            
            # Copy current config to backup
            import shutil
            shutil.copy2(self.config_file, backup_file)
            
            # Clean up old backups
            self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            logging.warning(f"Failed to create config backup: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            max_backups = self.config.get("max_backup_files", 5)
            backup_files = sorted(backup_dir.glob("config_backup_*.json"))
            
            if len(backup_files) > max_backups:
                for old_backup in backup_files[:-max_backups]:
                    old_backup.unlink()
                    
        except Exception as e:
            logging.warning(f"Failed to cleanup old backups: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        try:
            # Validate numeric values
            if not isinstance(self.config.get("auto_save_interval"), (int, float)) or self.config["auto_save_interval"] < 30:
                self.config["auto_save_interval"] = self.DEFAULT_CONFIG["auto_save_interval"]
                logging.warning("Invalid auto_save_interval, using default")
            
            if not isinstance(self.config.get("daily_goal"), int) or self.config["daily_goal"] < 1:
                self.config["daily_goal"] = self.DEFAULT_CONFIG["daily_goal"]
                logging.warning("Invalid daily_goal, using default")
            
            if not isinstance(self.config.get("min_word_length"), int) or self.config["min_word_length"] < 1:
                self.config["min_word_length"] = self.DEFAULT_CONFIG["min_word_length"]
                logging.warning("Invalid min_word_length, using default")
                
        except Exception as e:
            logging.error(f"Error validating config: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save immediately."""
        self.config[key] = value
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()
        logging.info("Configuration reset to defaults")


class WordDetector:
    """Handles word detection and counting logic with improved performance."""

    _COMMON_ABBREVS = frozenset({
        "i", "a", "an", "mr", "mrs", "dr", "prof", "etc", "vs",
        "i.e", "e.g", "a.m", "p.m",
    })
    
    def __init__(self, min_word_length: int = 2):
        # current_word is a transient buffer: it only holds characters between
        # word separators and is cleared on every word completion, listener stop,
        # focus change, pause, and stop_recording. No typed content persists.
        self.current_word = ""
        self.min_word_length = min_word_length
        self.word_pattern = re.compile(r'\b\w+\b')

        # Common word separators (only valid Key constants)
        self.separators = {Key.space, Key.enter, Key.tab}

        # Valid word characters (including hyphens and apostrophes)
        self.word_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'")
        
    def process_key(self, key: keyboard.KeyCode) -> Optional[int]:
        """Process a key press and return word count if a word is completed."""
        try:
            # Handle character keys
            if hasattr(key, 'char') and key.char:
                if key.char in self.word_chars:
                    self.current_word += key.char
                    return None
                else:
                    # Non-word character, check if we have a word
                    return self._check_word_completion()
            
            # Handle special keys
            elif key in self.separators:
                return self._check_word_completion()
            
            # Handle backspace
            elif key == Key.backspace and self.current_word:
                self.current_word = self.current_word[:-1]
                
        except AttributeError:
            pass
        
        return None
    
    def _check_word_completion(self) -> int:
        """Check if current text forms a valid word. No caching: the typed word
        must not live longer than this call for our privacy guarantees to hold.
        """
        word = self.current_word
        self.current_word = ""

        if not word:
            return 0

        word = word.strip()
        if not word:
            return 0

        return 1 if self._is_valid_word(word) else 0
    
    def _is_valid_word(self, word: str) -> bool:
        """Validate if a word meets the criteria for counting."""
        # Must meet minimum length
        if len(word) < self.min_word_length:
            return False
        
        # Must contain at least one alphabetic character
        if not any(c.isalpha() for c in word):
            return False
        
        # Check for common non-words (numbers only, single letters, etc.)
        if word.isdigit():
            return False
        
        # Check for common abbreviations and contractions
        if self._is_common_abbreviation(word):
            return True
        
        # Must not start or end with punctuation
        if word[0] in "-'" or word[-1] in "-'":
            return False
        
        return True
    
    def _is_common_abbreviation(self, word: str) -> bool:
        """Check if word is a common abbreviation that should be counted."""
        return word.lower() in self._COMMON_ABBREVS
    
    def reset(self) -> None:
        """Reset the detector state. Clears the transient current-word buffer."""
        self.current_word = ""


class Statistics:
    """Manages word count statistics and metrics with improved performance."""
    
    def __init__(self, wpm_history_size: int = 10):
        self.session_data = SessionData()
        self.wpm_history_size = wpm_history_size
        self.session_data.words_per_minute_history = deque(maxlen=wpm_history_size)
        self._last_update_time = 0
        self._update_interval = 0.1  # Update WPM every 100ms for better accuracy
        
    def start_session(self) -> None:
        """Start a new counting session."""
        self.session_data.reset()
        self.session_data.words_per_minute_history = deque(maxlen=self.wpm_history_size)
        self.session_data.start_time = datetime.now()
        self.session_data.session_id = str(uuid.uuid4())
        self._last_update_time = time.time()

    def add_words(self, n: int) -> None:
        """Increment word count by n and update WPM at most once per throttle window."""
        if n <= 0:
            return
        self.session_data.word_count += n
        current_time = time.time()
        if current_time - self._last_update_time >= self._update_interval:
            self._update_wpm(current_time)
            self._last_update_time = current_time
        
    def add_word(self) -> None:
        """Record a new word with improved WPM calculation."""
        self.add_words(1)
    
    def _update_wpm(self, current_time: float) -> None:
        """Update WPM calculation with improved algorithm."""
        if not self.session_data.start_time:
            return
            
        duration_minutes = (current_time - self.session_data.start_time.timestamp()) / 60.0
        if duration_minutes > 0:
            overall_wpm = self.session_data.word_count / duration_minutes
            
            # Add to history for rolling average (deque enforces maxlen)
            self.session_data.words_per_minute_history.append(overall_wpm)
            
            self.session_data.wpm = overall_wpm
    
    def get_session_duration(self) -> int:
        """Get session duration in seconds."""
        if self.session_data.start_time:
            return int((datetime.now() - self.session_data.start_time).total_seconds())
        return 0
    
    def get_average_wpm(self) -> float:
        """Calculate average words per minute from recent history."""
        if not self.session_data.words_per_minute_history:
            return 0.0
        
        # Use weighted average for more recent values
        weights = list(range(1, len(self.session_data.words_per_minute_history) + 1))
        total_weight = sum(weights)
        weighted_sum = sum(wpm * weight for wpm, weight in zip(self.session_data.words_per_minute_history, weights))
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def get_overall_wpm(self) -> float:
        """Get the current overall WPM for the session."""
        return self.session_data.wpm
    
    def get_session_data(self) -> SessionData:
        """Get the current session data."""
        return self.session_data
    
    def get_productivity_score(self) -> float:
        """Calculate a productivity score based on consistency and speed."""
        if not self.session_data.words_per_minute_history:
            return 0.0
        
        # Calculate consistency (lower variance = higher score)
        wpm_values = self.session_data.words_per_minute_history
        if len(wpm_values) < 2:
            return wpm_values[0] if wpm_values else 0.0
        
        mean_wpm = sum(wpm_values) / len(wpm_values)
        variance = sum((wpm - mean_wpm) ** 2 for wpm in wpm_values) / len(wpm_values)
        consistency = max(0, 1 - (variance / (mean_wpm ** 2 + 1)))
        
        # Combine speed and consistency
        return mean_wpm * consistency
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.session_data.reset()
        self._last_update_time = 0


class DataManager:
    """Manages data operations with improved error handling and performance."""
    
    def __init__(self, data_file: Union[str, Path] = "WordCountData.xlsx", flush_interval_seconds: int = 60):
        self.data_file = Path(data_file)
        self.backup_dir = self.data_file.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        # RLock: load_writing_sessions and add_session(flush=True) call helpers that
        # also take this lock; a plain Lock would deadlock on startup.
        self._save_lock = threading.RLock()
        self._data_cache: Optional[pd.DataFrame] = None
        self._pending_sessions: List[Dict[str, Any]] = []
        self._dirty = False
        self._last_flush_time = 0.0
        self._flush_interval_seconds = max(5, int(flush_interval_seconds))
        self._columns = [
            'Session ID',
            'Date and Time',
            'Word Count',
            'Duration (seconds)',
            'WPM',
            'Productivity Score',
        ]
        self._flush_backup_startup_done = False
        self._last_data_backup_date: Optional[date] = None

    def _ensure_cache_loaded(self) -> None:
        """Load data into cache if not already loaded."""
        if self._data_cache is not None:
            return
        if self.data_file.exists():
            self._data_cache = pd.read_excel(self.data_file)
        else:
            self._data_cache = pd.DataFrame(columns=self._columns)
        self._normalize_schema()

    def _normalize_schema(self) -> None:
        """Ensure cache has expected columns (for older xlsx files)."""
        if self._data_cache is None:
            return
        if 'Session ID' not in self._data_cache.columns:
            self._data_cache['Session ID'] = ""
        else:
            self._data_cache['Session ID'] = self._data_cache['Session ID'].fillna("").astype(str)

    def get_all_data(self, include_pending: bool = True) -> pd.DataFrame:
        """Get cached data, optionally including pending sessions."""
        with self._save_lock:
            self._ensure_cache_loaded()
            if include_pending and self._pending_sessions:
                pending_df = pd.DataFrame(self._pending_sessions)
                return pd.concat([self._data_cache, pending_df], ignore_index=True)
            return self._data_cache.copy()

    def add_session(self, session_data: SessionData, flush: bool = False) -> bool:
        """Upsert session row by Session ID; legacy rows with empty id still append."""
        last_hist = (
            session_data.words_per_minute_history[-1]
            if len(session_data.words_per_minute_history) else 0.0
        )
        session_row: Dict[str, Any] = {
            'Session ID': session_data.session_id or "",
            'Date and Time': session_data.start_time,
            'Word Count': session_data.word_count,
            'Duration (seconds)': session_data.duration,
            'WPM': session_data.wpm,
            'Productivity Score': last_hist,
        }
        sid = (session_data.session_id or "").strip()

        with self._save_lock:
            self._ensure_cache_loaded()
            self._normalize_schema()

            if sid:
                replaced_pending = False
                for i, row in enumerate(self._pending_sessions):
                    if str(row.get('Session ID', '') or '').strip() == sid:
                        self._pending_sessions[i] = session_row
                        replaced_pending = True
                        self._dirty = True
                        break
                if not replaced_pending:
                    found_in_cache = False
                    if not self._data_cache.empty and 'Session ID' in self._data_cache.columns:
                        mask = self._data_cache['Session ID'].astype(str).str.strip() == sid
                        if mask.any():
                            idx = int(self._data_cache[mask].index[-1])
                            for k, v in session_row.items():
                                self._data_cache.at[idx, k] = v
                            found_in_cache = True
                            self._dirty = True
                    if not found_in_cache:
                        self._pending_sessions.append(session_row)
                        self._dirty = True
            else:
                self._pending_sessions.append(session_row)
                self._dirty = True

            if flush:
                return self.flush_pending(force=True)
        return True

    def flush_pending(self, force: bool = False) -> bool:
        """Flush pending sessions and/or dirty cache to disk using atomic replace."""
        with self._save_lock:
            self._ensure_cache_loaded()
            self._normalize_schema()
            if not force and (time.time() - self._last_flush_time) < self._flush_interval_seconds:
                return True
            if not self._pending_sessions and not self._dirty:
                return True

            try:
                if self._pending_sessions:
                    pending_df = pd.DataFrame(self._pending_sessions)
                    if self._data_cache.empty:
                        combined = pending_df
                    else:
                        combined = pd.concat([self._data_cache, pending_df], ignore_index=True)
                else:
                    combined = self._data_cache.copy()

                self._maybe_backup_data_file(force=False)

                self.data_file.parent.mkdir(parents=True, exist_ok=True)

                temp_file = self.data_file.with_suffix(self.data_file.suffix + ".tmp")
                combined.to_excel(temp_file, index=False)
                temp_file.replace(self.data_file)

                self._data_cache = combined
                self._pending_sessions.clear()
                self._dirty = False
                self._last_flush_time = time.time()
                return True
            except Exception as e:
                logging.error(f"Error flushing session data: {e}")
                return False

    def save_session(self, session_data: SessionData) -> bool:
        """Save session data with error handling and backup."""
        return self.add_session(session_data, flush=False)

    def load_writing_sessions(self) -> List[WritingSession]:
        """Build WritingSession list from persisted rows (for analytics dashboard)."""
        with self._save_lock:
            self._ensure_cache_loaded()
            self._normalize_schema()
            df = self.get_all_data(include_pending=True)
        if df.empty or 'Date and Time' not in df.columns:
            return []

        sessions: List[WritingSession] = []
        for i, (_idx, row) in enumerate(df.iterrows()):
            try:
                ts = pd.to_datetime(row['Date and Time'])
                start_time = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.fromisoformat(str(ts))
                dur_sec = float(row.get('Duration (seconds)', 0) or 0)
                dur_min = dur_sec / 60.0
                end_time = start_time + timedelta(seconds=dur_sec)
                raw_sid = row.get('Session ID', "")
                if raw_sid is None or (isinstance(raw_sid, float) and pd.isna(raw_sid)):
                    sid = f"legacy_{i}"
                else:
                    sid = str(raw_sid).strip() or f"legacy_{i}"
                wc_raw = row.get('Word Count', 0)
                if wc_raw is None or (isinstance(wc_raw, float) and pd.isna(wc_raw)):
                    wc = 0
                else:
                    wc = int(wc_raw)
                w_raw = row.get('WPM', 0)
                wpm = 0.0 if w_raw is None or (isinstance(w_raw, float) and pd.isna(w_raw)) else float(w_raw)
                p_raw = row.get('Productivity Score', 0)
                prod = 0.0 if p_raw is None or (isinstance(p_raw, float) and pd.isna(p_raw)) else float(p_raw)
                sessions.append(WritingSession(
                    session_id=sid,
                    start_time=start_time,
                    end_time=end_time,
                    word_count=wc,
                    duration_minutes=dur_min,
                    wpm=wpm,
                    productivity_score=prod,
                    focus_score=prod,
                ))
            except Exception as ex:
                logging.warning(f"Skipping bad history row: {ex}")
        return sessions

    def backup_data_file_now(self) -> None:
        """Force an immediate on-disk backup (Tools menu)."""
        self._maybe_backup_data_file(force=True)

    def _maybe_backup_data_file(self, force: bool = False) -> None:
        """Back up at most once per app startup and once per calendar day unless forced."""
        if not self.data_file.exists():
            return
        today = date.today()
        if force:
            self._run_data_backup()
            self._last_data_backup_date = today
            return
        if not self._flush_backup_startup_done:
            self._flush_backup_startup_done = True
            self._run_data_backup()
            self._last_data_backup_date = today
            return
        if self._last_data_backup_date != today:
            self._last_data_backup_date = today
            self._run_data_backup()

    def _run_data_backup(self) -> None:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"data_backup_{timestamp}.xlsx"
            shutil.copy2(self.data_file, backup_file)
            self._cleanup_old_backups()
        except Exception as e:
            logging.warning(f"Failed to create data backup: {e}")
    
    def load_today_data(self) -> int:
        """Load today's word count from saved data."""
        try:
            df = self.get_all_data(include_pending=True)
            if df.empty:
                return 0
            df['Date and Time'] = pd.to_datetime(df['Date and Time'])
            
            # Get today's data
            today = datetime.now().date()
            today_data = df[df['Date and Time'].dt.date == today]
            
            if not today_data.empty:
                return today_data['Word Count'].sum()
                
        except Exception as e:
            logging.error(f"Error loading today's data: {e}")
        
        return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from saved data."""
        try:
            df = self.get_all_data(include_pending=True)
            if df.empty:
                return {}
            df['Date and Time'] = pd.to_datetime(df['Date and Time'])
            
            # Calculate various statistics
            total_words = df['Word Count'].sum()
            total_sessions = len(df)
            avg_words_per_session = df['Word Count'].mean()
            avg_wpm = df['WPM'].mean()
            
            # Last 7 and 30 days
            last_7_days = df[df['Date and Time'] > datetime.now() - timedelta(days=7)]['Word Count'].sum()
            last_30_days = df[df['Date and Time'] > datetime.now() - timedelta(days=30)]['Word Count'].sum()
            
            # Best session
            best_session = df.loc[df['Word Count'].idxmax()] if not df.empty else None
            
            return {
                'total_words': total_words,
                'total_sessions': total_sessions,
                'avg_words_per_session': avg_words_per_session,
                'avg_wpm': avg_wpm,
                'last_7_days': last_7_days,
                'last_30_days': last_30_days,
                'best_session': best_session.to_dict() if best_session is not None else None
            }
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {}
    
    def export_data(self, format: str = 'csv') -> Optional[str]:
        """Export data in specified format."""
        try:
            df = self.get_all_data(include_pending=True)
            if df.empty:
                return None
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format.lower() == 'csv':
                export_file = f"word_count_export_{timestamp}.csv"
                df.to_csv(export_file, index=False)
            elif format.lower() == 'json':
                export_file = f"word_count_export_{timestamp}.json"
                df.to_json(export_file, orient='records', indent=2)
            else:
                return None
                
            return export_file
            
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return None
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = sorted(self.backup_dir.glob("data_backup_*.xlsx"))
            if len(backup_files) > 10:
                for old_backup in backup_files[:-10]:
                    old_backup.unlink()
                    
        except Exception as e:
            logging.warning(f"Failed to cleanup old backups: {e}")


class AnalyticsDashboard:
    """Comprehensive analytics dashboard with visualizations."""
    
    def __init__(self, parent, analytics: AdvancedAnalytics):
        self.parent = parent
        self.analytics = analytics
        self.current_view = "overview"
        self._view_frames: Dict[str, tk.Frame] = {}
        
    def create_dashboard(self) -> tk.Frame:
        """Create the main dashboard interface."""
        dashboard_frame = ttk.Frame(self.parent)
        
        # Configure grid weights
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.rowconfigure(1, weight=1)
        
        # Navigation tabs
        nav_frame = ttk.Frame(dashboard_frame)
        nav_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        
        ttk.Button(nav_frame, text="Overview", command=lambda: self.show_view("overview")).pack(side='left', padx=5)
        ttk.Button(nav_frame, text="Trends", command=lambda: self.show_view("trends")).pack(side='left', padx=5)
        ttk.Button(nav_frame, text="Goals", command=lambda: self.show_view("goals")).pack(side='left', padx=5)
        ttk.Button(nav_frame, text="Achievements", command=lambda: self.show_view("achievements")).pack(side='left', padx=5)
        ttk.Button(nav_frame, text="Insights", command=lambda: self.show_view("insights")).pack(side='left', padx=5)
        
        # Content area
        self.content_frame = ttk.Frame(dashboard_frame)
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        
        # Show default view
        self.show_view("overview")
        
        return dashboard_frame
        
    def show_view(self, view_name: str) -> None:
        """Switch between different dashboard views."""
        if view_name == self.current_view and self.content_frame.winfo_children():
            return
        self.current_view = view_name

        for frame in self._view_frames.values():
            frame.pack_forget()

        if view_name in self._view_frames:
            self._view_frames[view_name].pack(fill='both', expand=True)
            return

        view_frame = ttk.Frame(self.content_frame)
        self._view_frames[view_name] = view_frame
        view_frame.pack(fill='both', expand=True)
        
        # Show selected view
        if view_name == "overview":
            self._create_overview_view(view_frame)
        elif view_name == "trends":
            self._create_trends_view(view_frame)
        elif view_name == "goals":
            self._create_goals_view(view_frame)
        elif view_name == "achievements":
            self._create_achievements_view(view_frame)
        elif view_name == "insights":
            self._create_insights_view(view_frame)
            
    def _create_overview_view(self, parent) -> None:
        """Create the overview dashboard."""
        # Header with key metrics
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 20))
        
        insights = self.analytics.get_writing_insights()
        
        # Key metrics cards
        metrics = [
            ("Current Streak", f"{insights.get('current_streak', 0)} days", "🔥"),
            ("Total Words", f"{insights.get('total_words_written', 0):,}", "📝"),
            ("Avg WPM", f"{insights.get('average_wpm', 0):.1f}", "⚡"),
            ("Consistency", f"{insights.get('consistency_score', 0)*100:.0f}%", "📊")
        ]
        
        for i, (label, value, icon) in enumerate(metrics):
            card = ttk.Frame(header_frame, relief='raised', borderwidth=1)
            card.pack(side='left', fill='both', expand=True, padx=5)
            
            ttk.Label(card, text=f"{icon} {label}", font=('Arial', 10, 'bold')).pack(pady=5)
            ttk.Label(card, text=value, font=('Arial', 16, 'bold')).pack(pady=5)
            
        # Recent activity chart
        chart_frame = ttk.LabelFrame(parent, text="Recent Activity", padding=10)
        chart_frame.pack(fill='both', expand=True, pady=10)
        
        self._create_weekly_activity_chart(chart_frame)
        
    def _create_trends_view(self, parent) -> None:
        """Create the trends analysis view."""
        # Time period selector
        period_frame = ttk.Frame(parent)
        period_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(period_frame, text="Time Period:").pack(side='left')
        period_var = tk.StringVar(value="30")
        ttk.Radiobutton(period_frame, text="7 days", variable=period_var, value="7").pack(side='left', padx=10)
        ttk.Radiobutton(period_frame, text="30 days", variable=period_var, value="30").pack(side='left', padx=10)
        ttk.Radiobutton(period_frame, text="90 days", variable=period_var, value="90").pack(side='left', padx=10)
        
        # Charts container
        charts_frame = ttk.Frame(parent)
        charts_frame.pack(fill='both', expand=True)
        
        # Left column - WPM trend
        left_frame = ttk.Frame(charts_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        wpm_frame = ttk.LabelFrame(left_frame, text="WPM Trend", padding=10)
        wpm_frame.pack(fill='both', expand=True)
        self._create_wpm_trend_chart(wpm_frame)
        
        # Right column - Word count trend
        right_frame = ttk.Frame(charts_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        words_frame = ttk.LabelFrame(right_frame, text="Daily Word Count", padding=10)
        words_frame.pack(fill='both', expand=True)
        self._create_word_count_chart(words_frame)
        
    def _create_goals_view(self, parent) -> None:
        """Create the goals tracking view."""
        # Add new goal button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Button(button_frame, text="Create New Goal", command=self._show_create_goal_dialog).pack(side='left')
        
        # Active goals
        goals_frame = ttk.LabelFrame(parent, text="Active Goals", padding=10)
        goals_frame.pack(fill='both', expand=True)
        
        # This would be populated with actual goals from the goal manager
        ttk.Label(goals_frame, text="No active goals. Create your first goal to get started!", 
                 font=('Arial', 12)).pack(pady=50)
                 
    def _create_achievements_view(self, parent) -> None:
        """Create the achievements view."""
        # Achievements grid
        achievements_frame = ttk.Frame(parent)
        achievements_frame.pack(fill='both', expand=True)
        
        # This would be populated with actual achievements
        ttk.Label(achievements_frame, text="Achievements will appear here as you unlock them!", 
                 font=('Arial', 12)).pack(pady=50)
                 
    def _create_insights_view(self, parent) -> None:
        """Create the insights view."""
        insights = self.analytics.get_writing_insights()
        
        # Insights cards
        insights_frame = ttk.Frame(parent)
        insights_frame.pack(fill='both', expand=True)
        
        insight_cards = [
            ("Best Writing Time", insights.get("best_writing_time", "Not enough data"), "🕐"),
            ("Most Productive Day", insights.get("most_productive_day", "Not enough data"), "📅"),
            ("Improvement Rate", f"{insights.get('improvement_rate', 0):+.1f}%", "📈"),
            ("Average Session", f"{insights.get('average_session_length', 0):.1f} min", "⏱️")
        ]
        
        for i, (label, value, icon) in enumerate(insight_cards):
            row = i // 2
            col = i % 2
            
            card = ttk.LabelFrame(insights_frame, text=f"{icon} {label}", padding=10)
            card.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)
            
            ttk.Label(card, text=value, font=('Arial', 14, 'bold')).pack(pady=10)
            
        insights_frame.grid_columnconfigure(0, weight=1)
        insights_frame.grid_columnconfigure(1, weight=1)
        
    def _create_weekly_activity_chart(self, parent) -> None:
        """Create a weekly activity heatmap chart."""
        try:
            fig = Figure(figsize=(10, 4))
            ax = fig.add_subplot(111)

            dates = []
            word_counts = []

            for i in range(7):
                day = datetime.now() - timedelta(days=i)
                daily_stats = self.analytics.get_daily_stats(day)
                dates.append(day.strftime('%A'))
                word_counts.append(daily_stats["words_written"])

            dates.reverse()
            word_counts.reverse()

            bars = ax.bar(dates, word_counts, color='skyblue', alpha=0.7)

            mx = max(word_counts) if word_counts else 0
            for bar, count in zip(bars, word_counts):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + max(mx * 0.01, 1.0),
                    f'{count:,}', ha='center', va='bottom', fontsize=10
                )

            ax.set_title('Last 7 Days Activity', fontsize=14, fontweight='bold')
            ax.set_ylabel('Words Written')
            ax.set_ylim(0, max(word_counts) * 1.1 if word_counts else 100)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            tw = canvas.get_tk_widget()
            tw.grid(row=0, column=0, sticky='nsew')
            parent.bind('<Destroy>', lambda _e: plt.close(fig), add='+')

        except Exception as e:
            ttk.Label(parent, text=f"Chart error: {e}").pack()

    def _create_wpm_trend_chart(self, parent) -> None:
        """Create WPM trend chart."""
        try:
            fig = Figure(figsize=(8, 6))
            ax = fig.add_subplot(111)

            recent_sessions = self.analytics.sessions[-20:] if len(self.analytics.sessions) >= 20 else self.analytics.sessions

            if recent_sessions:
                dates = [s.start_time.strftime('%m/%d') for s in recent_sessions]
                wpm_values = [s.wpm for s in recent_sessions]

                ax.plot(dates, wpm_values, marker='o', linewidth=2, markersize=6, color='green')
                ax.set_title('WPM Trend', fontsize=12, fontweight='bold')
                ax.set_ylabel('Words Per Minute')
                ax.set_xlabel('Date')
                for label in ax.get_xticklabels():
                    label.set_rotation(45)
                    label.set_ha('right')
            else:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('WPM Trend', fontsize=12, fontweight='bold')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
            parent.bind('<Destroy>', lambda _e: plt.close(fig), add='+')

        except Exception as e:
            ttk.Label(parent, text=f"Chart error: {e}").grid(row=0, column=0)

    def _create_word_count_chart(self, parent) -> None:
        """Create daily word count chart."""
        try:
            fig = Figure(figsize=(8, 6))
            ax = fig.add_subplot(111)

            dates = []
            word_counts = []

            for i in range(14):
                day = datetime.now() - timedelta(days=i)
                daily_stats = self.analytics.get_daily_stats(day)
                dates.append(day.strftime('%m/%d'))
                word_counts.append(daily_stats["words_written"])

            dates.reverse()
            word_counts.reverse()

            ax.bar(dates, word_counts, color='lightcoral', alpha=0.7)
            ax.set_title('Daily Word Count', fontsize=12, fontweight='bold')
            ax.set_ylabel('Words Written')
            ax.set_xlabel('Date')
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha('right')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
            parent.bind('<Destroy>', lambda _e: plt.close(fig), add='+')

        except Exception as e:
            ttk.Label(parent, text=f"Chart error: {e}").grid(row=0, column=0)
            
    def _show_create_goal_dialog(self) -> None:
        """Show dialog to create a new goal."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create New Goal")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Goal type
        ttk.Label(dialog, text="Goal Type:").pack(pady=5)
        goal_type_var = tk.StringVar(value="daily")
        ttk.Radiobutton(dialog, text="Daily", variable=goal_type_var, value="daily").pack()
        ttk.Radiobutton(dialog, text="Weekly", variable=goal_type_var, value="weekly").pack()
        ttk.Radiobutton(dialog, text="Monthly", variable=goal_type_var, value="monthly").pack()
        
        # Target words
        ttk.Label(dialog, text="Target Words:").pack(pady=5)
        target_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=target_var).pack(pady=5)
        
        # Duration (for weekly/monthly goals)
        ttk.Label(dialog, text="Duration (days):").pack(pady=5)
        duration_var = tk.StringVar(value="7")
        ttk.Entry(dialog, textvariable=duration_var).pack(pady=5)
        
        def create_goal():
            try:
                target_words = int(target_var.get())
                duration = int(duration_var.get())
                goal_type = goal_type_var.get()
                
                start_date = datetime.now()
                end_date = start_date + timedelta(days=duration)
                
                # This would create the goal in the goal manager
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
                
        ttk.Button(dialog, text="Create Goal", command=create_goal).pack(pady=20)

class SocialFeatures:
    """Social features for sharing and comparing with other writers."""
    
    def __init__(self):
        self.friends = []  # Would connect to actual social network
        self.challenges = []
        self.leaderboards = {}
        
    def create_writing_challenge(self, title: str, description: str, 
                               target_words: int, duration_days: int) -> Dict[str, Any]:
        """Create a new writing challenge."""
        challenge = {
            "id": f"challenge_{int(time.time())}",
            "title": title,
            "description": description,
            "target_words": target_words,
            "duration_days": duration_days,
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=duration_days),
            "participants": [],
            "leaderboard": []
        }
        self.challenges.append(challenge)
        return challenge
        
    def join_challenge(self, challenge_id: str, user_id: str) -> bool:
        """Join a writing challenge."""
        challenge = next((c for c in self.challenges if c["id"] == challenge_id), None)
        if challenge and user_id not in challenge["participants"]:
            challenge["participants"].append(user_id)
            return True
        return False
        
    def update_challenge_progress(self, challenge_id: str, user_id: str, words_written: int) -> None:
        """Update progress in a challenge."""
        challenge = next((c for c in self.challenges if c["id"] == challenge_id), None)
        if challenge:
            # Update leaderboard
            participant = next((p for p in challenge["leaderboard"] if p["user_id"] == user_id), None)
            if participant:
                participant["words_written"] += words_written
            else:
                challenge["leaderboard"].append({
                    "user_id": user_id,
                    "words_written": words_written
                })
            
            # Sort leaderboard
            challenge["leaderboard"].sort(key=lambda x: x["words_written"], reverse=True)
            
    def get_leaderboard(self, challenge_id: str) -> List[Dict[str, Any]]:
        """Get leaderboard for a challenge."""
        challenge = next((c for c in self.challenges if c["id"] == challenge_id), None)
        return challenge["leaderboard"] if challenge else []

class WordCountApp:
    def __init__(self, root: tk.Tk):
        """Initialize the WordCountApp with improved UI and functionality."""
        self.root = root
        self._app_data_dir = user_data_dir()
        migrate_legacy_data_to_app_dir(self._app_data_dir)
        self.setup_logging()
        self.config = Config(self._app_data_dir / "config.json")
        self.data_manager = DataManager(
            self._app_data_dir / "WordCountData.xlsx",
            flush_interval_seconds=self.config.get("data_flush_interval", 60),
        )
        self.word_detector = WordDetector(self.config.get("min_word_length", 2))
        self.statistics = Statistics(self.config.get("wpm_history_size", 10))
        self.app_state = AppState()
        self.keyboard_shortcuts = KeyboardShortcuts(self)
        self.app_focus_manager = AppFocusManager(self.config)
        self.analytics = AdvancedAnalytics()
        self.goal_manager = GoalManager(self.analytics)
        self.social_features = SocialFeatures()  # Initialize social features

        self.configure_root()
        self.initialize_variables()
        self.create_ui()
        self.load_data()
        self.setup_auto_save()
        self.update_display_timer()
        self.keyboard_shortcuts.bind_shortcuts()

        # Start the foreground-window watcher. It runs for the app's lifetime
        # and only triggers listener changes while the user is armed.
        self.focus_watcher = FocusWatcher(self.root, self._on_focus_change)
        self.focus_watcher.start()

        # Reconcile the Windows Run registry entry against the saved pref.
        try:
            want = bool(self.config.get("launch_on_startup", False))
            if want != is_launch_on_startup():
                set_launch_on_startup(want)
        except Exception as e:
            self.logger.warning(f"Startup reconcile failed: {e}")

        # If the user hasn't completed the onboarding wizard, show it shortly
        # after the main window appears.
        if not self.config.get("onboarding_completed", False):
            self.root.after(200, self._show_onboarding)

        # Offer to review crash logs from the previous run, if any.
        self.root.after(1200, self._check_for_previous_crashes)

    def _show_onboarding(self) -> None:
        try:
            OnboardingWizard(self.root, self)
        except Exception as e:
            self.logger.error(f"Failed to show onboarding: {e}")

    def _list_crash_logs(self) -> List[Path]:
        """Return crash .log files, newest first."""
        try:
            d = crashes_dir()
            return sorted(
                (p for p in d.glob("crash-*.log") if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            return []

    def _check_for_previous_crashes(self) -> None:
        """If crash logs exist, offer the user to view or email them. Shown once per launch."""
        if getattr(self, "_crash_prompt_shown", False):
            return
        self._crash_prompt_shown = True
        logs = self._list_crash_logs()
        if not logs:
            return
        newest = logs[0]
        msg = (
            f"WordCounter found {len(logs)} crash log(s) from previous runs.\n\n"
            f"Most recent: {newest.name}\n\n"
            "The logs contain a stack trace and system info only — no typed words, "
            "file contents, or window titles.\n\n"
            "Would you like to open the crash folder so you can review or email them?"
        )
        try:
            if messagebox.askyesno("Previous crash detected", msg, parent=self.root):
                self.open_crash_logs_folder()
        except Exception as e:
            self.logger.warning(f"Crash prompt failed: {e}")

    def open_crash_logs_folder(self) -> None:
        """Open the crashes directory in the OS file manager."""
        d = crashes_dir()
        if not open_in_file_manager(d):
            messagebox.showinfo(
                "Crash logs",
                f"Crash logs are stored at:\n{d}",
                parent=self.root,
            )

    def show_feedback_dialog(self) -> None:
        """Show a feedback dialog that composes a mailto: link."""
        win = tk.Toplevel(self.root)
        win.title("Send Feedback")
        win.geometry("560x440")
        win.transient(self.root)
        win.grab_set()

        frame = ttk.Frame(win, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Tell us what's working, what's broken, or what you'd like next.",
            wraplength=520,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        ttk.Label(
            frame,
            text=(
                "We only send what you type below, plus the app version and OS. "
                "No typed words, file contents, or window titles."
            ),
            wraplength=520,
            justify=tk.LEFT,
            foreground="#555",
        ).pack(anchor=tk.W, pady=(4, 8))

        text = tk.Text(frame, height=12, wrap=tk.WORD, font=("Segoe UI", 10))
        text.pack(fill=tk.BOTH, expand=True)
        text.focus_set()

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(10, 0))

        def do_send() -> None:
            user_text = text.get("1.0", tk.END).strip()
            body_extra = f"User note:\n{user_text}" if user_text else ""
            url = build_feedback_mailto(body_extra=body_extra)
            try:
                webbrowser.open(url)
            except Exception as e:
                self.logger.warning(f"Failed to open mailto: {e}")
                messagebox.showinfo(
                    "Send Feedback",
                    f"Could not open your email client automatically.\n\n"
                    f"Please email {FEEDBACK_EMAIL} with:\n\n{user_text}",
                    parent=win,
                )
                return
            win.destroy()

        ttk.Button(btns, text="Open Email", command=do_send).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side=tk.RIGHT, padx=(0, 8))

    def setup_logging(self) -> None:
        """Configure logging for the application."""
        self._app_data_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._app_data_dir / "word_counter.log"
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def configure_root(self) -> None:
        """Configure the root window properties."""
        self.root.title("Word Counter Pro")
        self.root.geometry(self.config.get("window_geometry"))
        self.root.minsize(720, 520)

        # ttk theme: prefer the configured one, then the native Windows theme,
        # then a clean cross-platform fallback.
        self.style = ttk.Style()
        available = set(self.style.theme_names())
        preferred = [self.config.get("theme"), "aqua", "vista", "xpnative", "clam", "default"]
        for name in preferred:
            if name in available:
                try:
                    self.style.theme_use(name)
                    break
                except tk.TclError:
                    continue

        # Unified typography. Segoe UI is the Windows system font; falls back
        # gracefully on other platforms.
        base_family = "Segoe UI"
        self.root.option_add("*Font", (base_family, 10))
        self.style.configure(".", font=(base_family, 10))
        self.style.configure("TLabel", font=(base_family, 10))
        self.style.configure("TButton", font=(base_family, 10), padding=(12, 6))
        self.style.configure("TLabelframe.Label", font=(base_family, 10, "bold"))
        self.style.configure("TMenubutton", font=(base_family, 10))

        # Hero header styles.
        self.style.configure("Hero.TLabel", font=(base_family, 20, "bold"))
        self.style.configure("HeroSub.TLabel", font=(base_family, 10), foreground="#666666")

        # Stats: label vs value contrast.
        self.style.configure("StatLabel.TLabel", font=(base_family, 10), foreground="#555555")
        self.style.configure("StatValue.TLabel", font=(base_family, 16, "bold"))
        self.style.configure("StatValueMuted.TLabel", font=(base_family, 14))

        # Legacy aliases used elsewhere in the app.
        self.style.configure("Title.TLabel", font=(base_family, 14, "bold"))
        self.style.configure("Stats.TLabel", font=(base_family, 11))
        self.style.configure("Success.TLabel", foreground="#1e8e3e")
        self.style.configure("Warning.TLabel", foreground="#d97706")

        # Primary action button (used for Start Recording).
        self.style.configure(
            "Accent.TButton",
            font=(base_family, 10, "bold"),
            padding=(14, 8),
        )

        # Status bar: flat, padded, subtle tint.
        self.style.configure(
            "StatusBar.TLabel",
            font=(base_family, 9),
            background="#f2f2f2",
            foreground="#333333",
            padding=(10, 6),
        )

    def initialize_variables(self) -> None:
        """Initialize instance variables."""
        self.listener: Optional[keyboard.Listener] = None
        self._listener_lock = threading.Lock()
        self._current_focus_app: str = ""
        self.today_total = 0
        self.daily_goal = self.config.get("daily_goal", 1000)
        self.last_notification_time = 0
        self.notification_cooldown = 5  # seconds between notifications
        self._pending_word_count = 0
        self._pending_word_lock = threading.Lock()
        self._goal_notified_date: Optional[date] = None
        self._daily_goal_save_job: Optional[Any] = None

    def create_ui(self) -> None:
        """Create the user interface with improved layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=(18, 16, 18, 12))
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Hero header
        header = ttk.Frame(main_frame)
        header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 14))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Word Counter Pro", style="Hero.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Label(
            header,
            text="Tracks words only inside your writing apps. Nothing else.",
            style="HeroSub.TLabel",
        ).grid(row=1, column=0, sticky=tk.W, pady=(2, 0))

        # Statistics Frame
        self.create_statistics_frame(main_frame)
        
        # Progress Frame
        self.create_progress_frame(main_frame)
        
        # Control Frame
        self.create_control_frame(main_frame)
        
        # Status Bar
        self.create_status_bar(main_frame)
        
        # Menu Bar
        self.create_menu_bar()

    def create_statistics_frame(self, parent):
        """Create the statistics display frame."""
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding=(14, 10))
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=6)
        stats_frame.columnconfigure(1, weight=1)

        row_pady = (2, 2)

        ttk.Label(stats_frame, text="Current session", style="StatLabel.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 16), pady=row_pady
        )
        self.session_count_label = ttk.Label(stats_frame, text="0 words", style="StatValue.TLabel")
        self.session_count_label.grid(row=0, column=1, sticky=tk.W, pady=row_pady)

        ttk.Label(stats_frame, text="Today's total", style="StatLabel.TLabel").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 16), pady=row_pady
        )
        self.today_count_label = ttk.Label(stats_frame, text="0 words", style="StatValue.TLabel")
        self.today_count_label.grid(row=1, column=1, sticky=tk.W, pady=row_pady)

        ttk.Label(stats_frame, text="Words / minute", style="StatLabel.TLabel").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 16), pady=row_pady
        )
        self.wpm_label = ttk.Label(stats_frame, text="0 WPM", style="StatValueMuted.TLabel")
        self.wpm_label.grid(row=2, column=1, sticky=tk.W, pady=row_pady)

        ttk.Label(stats_frame, text="Session time", style="StatLabel.TLabel").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 16), pady=row_pady
        )
        self.duration_label = ttk.Label(stats_frame, text="00:00:00", style="StatValueMuted.TLabel")
        self.duration_label.grid(row=3, column=1, sticky=tk.W, pady=row_pady)

    def create_progress_frame(self, parent):
        """Create the progress display frame."""
        progress_frame = ttk.LabelFrame(parent, text="Daily Progress", padding="10")
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress Label
        self.progress_label = ttk.Label(
            progress_frame, 
            text=f"0 / {self.daily_goal} words (0%)",
            style="Stats.TLabel"
        )
        self.progress_label.grid(row=1, column=0, columnspan=2)
        
        # Goal Settings
        ttk.Label(progress_frame, text="Daily Goal:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.goal_var = tk.StringVar(value=str(self.daily_goal))
        goal_spinbox = ttk.Spinbox(
            progress_frame,
            from_=100,
            to=10000,
            increment=100,
            textvariable=self.goal_var,
            width=10,
            command=self.update_daily_goal
        )
        goal_spinbox.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))

    def create_control_frame(self, parent):
        """Create the control buttons frame."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=3, column=0, pady=(18, 10))

        # Start Button (primary action)
        self.start_button = ttk.Button(
            control_frame,
            text="▶  Start Recording",
            command=self.start_recording,
            width=20,
            style="Accent.TButton",
        )
        self.start_button.grid(row=0, column=0, padx=6)

        # Pause Button
        self.pause_button = ttk.Button(
            control_frame,
            text="⏸  Pause",
            command=self.toggle_pause,
            state=tk.DISABLED,
            width=18,
        )
        self.pause_button.grid(row=0, column=1, padx=6)

        # Stop Button
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹  Stop",
            command=self.stop_recording,
            state=tk.DISABLED,
            width=18,
        )
        self.stop_button.grid(row=0, column=2, padx=6)

    def create_status_bar(self, parent):
        """Create the status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            parent,
            textvariable=self.status_var,
            style="StatusBar.TLabel",
            anchor=tk.W,
        )
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(12, 0))

    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data...", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Reset Configuration", command=self.reset_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Analytics Dashboard", command=self.show_analytics_dashboard)
        view_menu.add_separator()
        view_menu.add_command(label="Statistics", command=self.show_statistics)
        view_menu.add_command(label="History", command=self.show_history)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Writing Apps...", command=self.show_writing_apps_settings)
        tools_menu.add_command(label="About Privacy...", command=self.show_privacy_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="Setup Wizard...", command=self._show_onboarding)
        if IS_MACOS:
            tools_menu.add_command(label="Check macOS Permissions...", command=self.show_mac_permissions_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="Keyboard Shortcuts", command=self.keyboard_shortcuts.show_shortcuts_help)
        tools_menu.add_separator()
        tools_menu.add_command(label="Backup Data", command=self.backup_data)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Send Feedback...", command=self.show_feedback_dialog)
        help_menu.add_command(label="Open Crash Logs Folder", command=self.open_crash_logs_folder)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def update_display(self):
        """Update all display elements."""
        # Update session count
        session_data = self.statistics.get_session_data()
        session_count = session_data.word_count
        self.session_count_label.config(text=f"{session_count} words")
        
        # Update today's total
        total = self.today_total + session_count
        self.today_count_label.config(text=f"{total} words")
        
        # Update progress
        progress = min((total / self.daily_goal) * 100, 100)
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{total} / {self.daily_goal} words ({progress:.1f}%)")
        
        # Update progress label style based on achievement
        if total >= self.daily_goal:
            self.progress_label.config(style="Success.TLabel")
            self._show_goal_achievement_notification()
        elif progress >= 75:
            self.progress_label.config(style="Warning.TLabel")
        else:
            self.progress_label.config(style="Stats.TLabel")
        
        # Update WPM
        wpm = self.statistics.get_overall_wpm()
        self.wpm_label.config(text=f"{wpm:.1f} WPM")
        
        # Update duration
        duration = self.statistics.get_session_duration()
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.duration_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def update_display_timer(self):
        """Timer to update display regularly."""
        if self.app_state.recording:
            self._apply_pending_word_counts()
            if not self.app_state.paused:
                self.update_display()
        self.root.after(1000, self.update_display_timer)

    def _apply_pending_word_counts(self) -> None:
        """Apply pending word counts from background listener thread."""
        with self._pending_word_lock:
            pending = self._pending_word_count
            self._pending_word_count = 0
        
        if pending:
            self.statistics.add_words(pending)

    def on_key_press(self, key):
        """Handle keyboard input. Belt-and-suspenders allowlist check.

        Under the strong-allowlist model the listener should already be stopped
        whenever the user is not in a writing app (see FocusWatcher). This check
        is a defensive guard for the moment between focus-change events.
        """
        if self.app_state.recording and not self.app_state.paused:
            if not self.app_focus_manager.is_writing_context():
                return

            word_count = self.word_detector.process_key(key)
            if word_count:
                with self._pending_word_lock:
                    self._pending_word_count += word_count
    
    def _show_goal_achievement_notification(self):
        """Show notification when daily goal is achieved (at most once per calendar day)."""
        today_d = datetime.now().date()
        if self._goal_notified_date == today_d:
            return
        session_data = self.statistics.get_session_data()
        total = self.today_total + session_data.word_count
        if total < self.daily_goal:
            return
        if not self.config.get("show_notifications", True):
            return
        self._goal_notified_date = today_d
        self.last_notification_time = time.time()
        messagebox.showinfo(
            "Goal Achieved! 🎉",
            f"Congratulations! You've reached your daily goal of {self.daily_goal} words!"
        )

    def _should_listen(self) -> bool:
        """True iff we should currently have a keyboard listener running."""
        return (
            self.app_state.recording
            and not self.app_state.paused
            and self.app_focus_manager.is_writing_context()
        )

    def _ensure_listener_running(self) -> None:
        with self._listener_lock:
            if self.listener is not None:
                return
            try:
                self.listener = keyboard.Listener(on_press=self.on_key_press)
                self.listener.start()
                self.logger.info(f"Listener started (focus={self._current_focus_app or 'unknown'})")
            except Exception as e:
                self.logger.error(f"Failed to start keyboard listener: {e}")
                self.listener = None

    def _ensure_listener_stopped(self) -> None:
        with self._listener_lock:
            if self.listener is None:
                return
            try:
                self.listener.stop()
            except Exception as e:
                self.logger.warning(f"Error stopping listener: {e}")
            self.listener = None
            # The in-memory current-word buffer must not survive a focus blur.
            try:
                self.word_detector.reset()
            except Exception:
                pass
            self.logger.info("Listener stopped")

    def _reconcile_listener(self) -> None:
        """Make the listener's running state match _should_listen()."""
        if self._should_listen():
            self._ensure_listener_running()
        else:
            self._ensure_listener_stopped()

    def _on_focus_change(self, process_name: str) -> None:
        """Called on the Tk main thread when the foreground window changes."""
        self._current_focus_app = process_name or ""
        self.app_focus_manager._invalidate_cache()
        self._reconcile_listener()
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        if not self.app_state.recording:
            self.status_var.set("Ready")
            return
        if self.app_state.paused:
            self.status_var.set("Paused")
            return
        if self.app_focus_manager.is_writing_context():
            focus = friendly_app_name(self._current_focus_app) or "writing app"
            self.status_var.set(f"Recording - {focus}")
        else:
            self.status_var.set("Armed - waiting for a writing app...")

    def start_recording(self):
        """Arm the recorder. The keyboard listener will run only while a writing app is focused."""
        try:
            self.statistics.start_session()

            self.app_state.recording = True
            self.app_state.paused = False

            self.app_focus_manager.update_context()
            self._current_focus_app = self.app_focus_manager.current_app or ""

            self._reconcile_listener()
            self.update_button_states()
            self._update_status_bar()

            self.logger.info("Recording armed")

        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            messagebox.showerror("Error", "Failed to start recording")

    def toggle_pause(self):
        """Toggle pause state."""
        self.app_state.paused = not self.app_state.paused
        self.pause_button.config(text="▶ Resume" if self.app_state.paused else "⏸ Pause")
        self._reconcile_listener()
        self._update_status_bar()
        self.logger.info(f"Recording {'paused' if self.app_state.paused else 'resumed'}")

    def stop_recording(self):
        """Stop the recording session."""
        try:
            self._ensure_listener_stopped()

            session_data = self.statistics.get_session_data()
            if session_data.word_count > 0:
                # Update session duration before saving
                session_data.duration = self.statistics.get_session_duration()
                if self.data_manager.save_session(session_data):
                    self.data_manager.flush_pending(force=True)
                    self.today_total += session_data.word_count
                    self.logger.info(f"Session saved: {session_data.word_count} words")
                    prod_score = self.statistics.get_productivity_score()
                    hist = session_data.words_per_minute_history
                    last_hist = float(hist[-1]) if len(hist) else float(session_data.wpm)
                    ws = WritingSession(
                        session_id=session_data.session_id,
                        start_time=session_data.start_time or datetime.now(),
                        end_time=datetime.now(),
                        word_count=session_data.word_count,
                        duration_minutes=session_data.duration / 60.0,
                        wpm=session_data.wpm,
                        productivity_score=last_hist,
                        focus_score=float(prod_score),
                    )
                    self.analytics.add_session(ws)
                else:
                    messagebox.showwarning("Warning", "Failed to save session data")
            
            # Reset
            self.app_state.recording = False
            self.app_state.paused = False
            self.statistics.reset()
            self.word_detector.reset()
            
            self.update_button_states()
            self.update_display()
            self._update_status_bar()

            self.logger.info("Recording stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            messagebox.showerror("Error", "Failed to stop recording")

    def update_button_states(self):
        """Update button states based on recording status."""
        if self.app_state.recording:
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED, text="⏸ Pause")
            self.stop_button.config(state=tk.DISABLED)

    def load_data(self):
        """Load today's word count from saved data."""
        try:
            self.today_total = self.data_manager.load_today_data()
            self.analytics.bulk_load_sessions(self.data_manager.load_writing_sessions())
            self.update_display()
            self.logger.info(f"Loaded today's total: {self.today_total} words")

        except Exception as e:
            self.logger.error(f"Error loading data: {e}")

    def setup_auto_save(self):
        """Setup automatic session saving."""
        def auto_save():
            if (self.app_state.recording and 
                self.app_state.auto_save_enabled and 
                self.statistics.get_session_data().word_count > 0):
                
                session_data = self.statistics.get_session_data()
                session_data.duration = self.statistics.get_session_duration()
                
                if self.data_manager.save_session(session_data):
                    self.data_manager.flush_pending(force=False)
                    self.status_var.set("Auto-saved")
                    self.root.after(2000, self._update_status_bar)
                    self.logger.info("Auto-save completed")
                else:
                    self.logger.warning("Auto-save failed")
            
            interval = self.config.get("auto_save_interval", 300) * 1000
            self.root.after(interval, auto_save)
        
        interval = self.config.get("auto_save_interval", 300) * 1000
        self.root.after(interval, auto_save)

    def update_daily_goal(self):
        """Update the daily goal setting (debounced write to config.json)."""
        try:
            self.daily_goal = int(self.goal_var.get())
        except ValueError:
            return
        self.update_display()
        if self._daily_goal_save_job is not None:
            try:
                self.root.after_cancel(self._daily_goal_save_job)
            except (tk.TclError, ValueError):
                pass
        self._daily_goal_save_job = self.root.after(500, self._persist_daily_goal)

    def _persist_daily_goal(self) -> None:
        self._daily_goal_save_job = None
        try:
            self.config.set("daily_goal", int(self.goal_var.get()))
        except ValueError:
            pass

    def export_data(self):
        """Export data to CSV or JSON."""
        try:
            # Ask user for format
            format_choice = messagebox.askyesnocancel(
                "Export Format",
                "Choose export format:\n\nYes = CSV\nNo = JSON\nCancel = Cancel"
            )
            
            if format_choice is None:  # Cancel
                return
                
            format_type = 'csv' if format_choice else 'json'
            export_file = self.data_manager.export_data(format_type)
            
            if export_file:
                messagebox.showinfo("Export Complete", f"Data exported to {export_file}")
            else:
                messagebox.showwarning("No Data", "No data to export")
                
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            messagebox.showerror("Error", "Failed to export data")
    
    def reset_config(self):
        """Reset configuration to defaults."""
        try:
            response = messagebox.askyesno(
                "Reset Configuration",
                "Are you sure you want to reset all configuration to defaults?\n\nThis will restart the application."
            )
            
            if response:
                self.config.reset_to_defaults()
                messagebox.showinfo(
                    "Configuration Reset",
                    "Configuration has been reset to defaults.\nThe application will restart."
                )
                self.root.after(1000, self._restart_application)
                
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            messagebox.showerror("Error", "Failed to reset configuration")
    
    def backup_data(self):
        """Manually backup data."""
        try:
            if self.data_manager.data_file.exists():
                self.data_manager.backup_data_file_now()
                messagebox.showinfo("Backup Complete", "Data backup created successfully")
            else:
                messagebox.showwarning("No Data", "No data to backup")
                
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            messagebox.showerror("Error", "Failed to create backup")
    
    def _restart_application(self):
        """Restart the application."""
        try:
            self.root.destroy()
            # Restart the application
            main()
        except Exception as e:
            self.logger.error(f"Error restarting application: {e}")
            messagebox.showerror("Error", "Failed to restart application")

    def show_statistics(self):
        """Show detailed statistics window."""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Detailed Statistics")
        stats_window.geometry("600x500")
        
        # Create main frame
        main_frame = ttk.Frame(stats_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Detailed Statistics", font=("Helvetica", 14, "bold")).pack(pady=(0, 10))
        
        try:
            stats = self.data_manager.get_statistics()
            
            if stats:
                # Create statistics display
                stats_frame = ttk.LabelFrame(main_frame, text="Overall Statistics", padding="10")
                stats_frame.pack(fill=tk.X, pady=(0, 10))
                
                stats_text = f"""
Total Words Written: {stats['total_words']:,}
Total Sessions: {stats['total_sessions']}
Average Words per Session: {stats['avg_words_per_session']:.1f}
Average WPM: {stats['avg_wpm']:.1f}

Last 7 Days: {stats['last_7_days']:,} words
Last 30 Days: {stats['last_30_days']:,} words
                """
                
                ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack()
                
                # Best session info
                if stats['best_session']:
                    best_frame = ttk.LabelFrame(main_frame, text="Best Session", padding="10")
                    best_frame.pack(fill=tk.X, pady=(0, 10))
                    
                    best_date = pd.to_datetime(stats['best_session']['Date and Time']).strftime('%Y-%m-%d %H:%M')
                    best_text = f"""
Date: {best_date}
Words: {stats['best_session']['Word Count']:,}
Duration: {stats['best_session']['Duration (seconds)'] / 60:.1f} minutes
WPM: {stats['best_session']['WPM']:.1f}
                    """
                    
                    ttk.Label(best_frame, text=best_text, justify=tk.LEFT).pack()
                
                # Current session info
                current_frame = ttk.LabelFrame(main_frame, text="Current Session", padding="10")
                current_frame.pack(fill=tk.X)
                
                session_data = self.statistics.get_session_data()
                current_text = f"""
Words: {session_data.word_count}
Duration: {self.statistics.get_session_duration() / 60:.1f} minutes
Current WPM: {self.statistics.get_overall_wpm():.1f}
Productivity Score: {self.statistics.get_productivity_score():.1f}
                """
                
                ttk.Label(current_frame, text=current_text, justify=tk.LEFT).pack()
                
            else:
                ttk.Label(main_frame, text="No data available", font=("Helvetica", 12)).pack(pady=20)
                
        except Exception as e:
            self.logger.error(f"Error showing statistics: {e}")
            ttk.Label(main_frame, text="Error loading statistics", foreground="red").pack(pady=20)

    def show_history(self):
        """Show writing history window."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Writing History")
        history_window.geometry("700x500")
        
        # Create main frame
        main_frame = ttk.Frame(history_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Writing History", font=("Helvetica", 14, "bold")).pack(pady=(0, 10))
        
        # Create treeview for history
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ("Date", "Words", "Duration", "WPM", "Productivity")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        # Configure columns
        column_widths = {"Date": 150, "Words": 100, "Duration": 100, "WPM": 80, "Productivity": 100}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths.get(col, 100))
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load data
        try:
            df = self.data_manager.get_all_data(include_pending=True)
            if not df.empty:
                df = df.sort_values('Date and Time', ascending=False)
                
                for _, row in df.iterrows():
                    date_str = pd.to_datetime(row['Date and Time']).strftime('%Y-%m-%d %H:%M')
                    duration_min = row.get('Duration (seconds)', 0) / 60
                    productivity = row.get('Productivity Score', 0)
                    
                    tree.insert("", "end", values=(
                        date_str,
                        f"{int(row['Word Count']):,}",
                        f"{duration_min:.1f} min",
                        f"{row.get('WPM', 0):.1f}",
                        f"{productivity:.1f}"
                    ))
            else:
                ttk.Label(main_frame, text="No history data available", font=("Helvetica", 12)).pack(pady=20)
                
        except Exception as e:
            self.logger.error(f"Error showing history: {e}")
            ttk.Label(main_frame, text="Error loading history", foreground="red").pack(pady=20)

    def show_writing_apps_settings(self):
        """Show the writing-app allowlist settings dialog."""
        win = tk.Toplevel(self.root)
        win.title("Writing Apps")
        win.geometry("600x520")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (600 // 2)
        y = (win.winfo_screenheight() // 2) - (520 // 2)
        win.geometry(f"600x520+{x}+{y}")

        main_frame = ttk.Frame(win, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        intro = ttk.Label(
            main_frame,
            text=(
                "The keyboard listener only runs while one of these apps is focused.\n"
                "When you switch to anything else, the listener stops and no keystrokes\n"
                "reach this process. Add the writing apps you want tracked."
            ),
            justify=tk.LEFT,
            wraplength=540,
        )
        intro.pack(anchor=tk.W, pady=(0, 15))

        allowed_frame = ttk.LabelFrame(main_frame, text="Allowed Writing Apps", padding="10")
        allowed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        list_row = ttk.Frame(allowed_frame)
        list_row.pack(fill=tk.BOTH, expand=True)

        allowed_listbox = tk.Listbox(list_row, height=10)
        allowed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_row, orient=tk.VERTICAL, command=allowed_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        allowed_listbox.config(yscrollcommand=scrollbar.set)

        buttons_frame = ttk.Frame(allowed_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        # Parallel list mirroring the listbox rows -> process names, since the
        # listbox displays friendly labels but the allowlist is keyed on *.exe.
        row_process_names: List[str] = []

        def refresh_allowed_list():
            allowed_listbox.delete(0, tk.END)
            row_process_names.clear()
            pairs = [(friendly_app_name(p), p) for p in self.app_focus_manager.get_allowed_apps()]
            pairs.sort(key=lambda pr: pr[0].lower())
            for label, process_name in pairs:
                allowed_listbox.insert(tk.END, label)
                row_process_names.append(process_name)

        def add_app():
            app_name = simpledialog.askstring(
                "Add Writing App",
                "Enter the executable name (e.g., obsidian.exe):",
                parent=win,
            )
            if app_name:
                name = app_name.strip().lower()
                if name and not name.endswith(".exe"):
                    name = name + ".exe"
                if name:
                    self.app_focus_manager.add_allowed_app(name)
                    refresh_allowed_list()

        def remove_app():
            selection = allowed_listbox.curselection()
            if selection:
                idx = selection[0]
                if 0 <= idx < len(row_process_names):
                    self.app_focus_manager.remove_allowed_app(row_process_names[idx])
                    refresh_allowed_list()

        def reset_defaults():
            if messagebox.askyesno(
                "Reset to defaults",
                "Replace the allowlist with the shipped default writing apps?",
                parent=win,
            ):
                self.app_focus_manager.set_allowed_apps(Config.DEFAULT_ALLOWED_APPS)
                refresh_allowed_list()

        ttk.Button(buttons_frame, text="Add...", command=add_app).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Remove Selected", command=remove_app).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Reset to Defaults", command=reset_defaults).pack(side=tk.LEFT)

        context_frame = ttk.LabelFrame(main_frame, text="Current Focus", padding="10")
        context_frame.pack(fill=tk.X, pady=(0, 15))

        self.context_label = ttk.Label(context_frame, text="Click 'Refresh' to inspect the focused window.")
        self.context_label.pack(anchor=tk.W)

        def update_context():
            self.app_focus_manager.update_context()
            app_name = self.app_focus_manager.current_app or ""
            window_title = self.app_focus_manager.current_window_title or "Unknown"
            is_writing = self.app_focus_manager.is_writing_context()
            friendly = friendly_app_name(app_name) if app_name else "Unknown"
            app_line = f"{friendly} ({app_name})" if app_name else "Unknown"
            self.context_label.config(text=(
                f"Application: {app_line}\n"
                f"Window:      {window_title}\n"
                f"In writing app: {'Yes' if is_writing else 'No'}"
            ))

        ttk.Button(context_frame, text="Refresh", command=update_context).pack(anchor=tk.W, pady=(5, 0))

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(bottom_frame, text="Close", command=win.destroy).pack(side=tk.RIGHT)

        refresh_allowed_list()
        update_context()

    def show_privacy_dialog(self):
        """Show an explicit privacy statement. Designed to be the answer to
        'what are you actually doing with my keystrokes?'."""
        win = tk.Toplevel(self.root)
        win.title("Privacy")
        win.geometry("620x520")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (620 // 2)
        y = (win.winfo_screenheight() // 2) - (520 // 2)
        win.geometry(f"620x520+{x}+{y}")

        main = ttk.Frame(win, padding="20")
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Privacy", font=("Helvetica", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))

        bg = self.root.cget("bg")
        body = tk.Text(main, wrap=tk.WORD, height=20, relief=tk.FLAT,
                       background=bg, borderwidth=0)
        body.pack(fill=tk.BOTH, expand=True)

        statement = (
            "WordCounter is a writing-app tracker, not a keystroke logger.\n\n"
            "What we actually do:\n"
            "  - A foreground-window hook watches which app is focused.\n"
            "  - The keyboard listener is only created while one of your\n"
            "    allowlisted writing apps is focused. When you alt-tab to\n"
            "    anything else, the listener is stopped and this process\n"
            "    receives zero keystrokes.\n"
            "  - We only store aggregate counts (words, duration, WPM) per\n"
            "    session and per day.\n"
            "  - A short in-memory buffer holds the characters of the word you\n"
            "    are currently typing. It is cleared on every word boundary,\n"
            "    pause, stop, and app switch. No typed content is cached,\n"
            "    hashed, or written to disk.\n\n"
            "What we do NOT do:\n"
            "  - No cloud uploads. No telemetry. No network calls in v1.\n"
            "  - No screenshotting, clipboard access, or file scanning.\n"
            "  - No logging of what you type, in any app, ever.\n\n"
            "Your allowlist lives in config.json (under %APPDATA%\\WordCounterPro\\).\n"
            "You can add or remove apps any time from Tools > Writing Apps.\n\n"
            "The source is open. Audit AppFocusManager, FocusWatcher, and\n"
            "WordDetector in wordcounter.py to verify every claim above."
        )
        body.insert("1.0", statement)
        body.config(state=tk.DISABLED)

        bottom = ttk.Frame(main)
        bottom.pack(fill=tk.X, pady=(15, 0))
        ttk.Button(bottom, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    def show_mac_permissions_dialog(self) -> None:
        """macOS: compact permission re-check dialog with deep-links."""
        if not IS_MACOS:
            return

        win = tk.Toplevel(self.root)
        win.title("macOS Permissions")
        win.geometry("520x320")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (520 // 2)
        y = (win.winfo_screenheight() // 2) - (320 // 2)
        win.geometry(f"520x320+{x}+{y}")

        main = ttk.Frame(win, padding="20")
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="macOS Permissions", font=("Helvetica", 16, "bold")).pack(
            anchor=tk.W, pady=(0, 6)
        )
        ttk.Label(
            main,
            text=(
                "WordCounter needs both Accessibility (to see which app is "
                "focused) and Input Monitoring (to count words) granted to "
                "this process."
            ),
            wraplength=470, justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        acc_var = tk.StringVar()
        inp_var = tk.StringVar()

        def label(value: Optional[bool]) -> str:
            if value is True:
                return "Granted"
            if value is False:
                return "Not granted"
            return "Unknown"

        def refresh() -> None:
            acc_var.set(label(mac_accessibility_granted()))
            inp_var.set(label(mac_input_monitoring_granted()))

        grid = ttk.Frame(main)
        grid.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(grid, text="Accessibility:", width=18, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Label(grid, textvariable=acc_var, width=14).grid(row=0, column=1, sticky=tk.W, padx=(4, 12))
        ttk.Button(grid, text="Open Settings",
                   command=lambda: open_mac_privacy_pane("accessibility")).grid(row=0, column=2, sticky=tk.W)

        ttk.Label(grid, text="Input Monitoring:", width=18, anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Label(grid, textvariable=inp_var, width=14).grid(row=1, column=1, sticky=tk.W, padx=(4, 12))
        ttk.Button(grid, text="Open Settings",
                   command=lambda: open_mac_privacy_pane("input_monitoring")).grid(row=1, column=2, sticky=tk.W)

        refresh()

        # Poll so statuses update as the user flips the toggles.
        poll_job: Dict[str, Optional[str]] = {"id": None}

        def poll() -> None:
            refresh()
            poll_job["id"] = win.after(1500, poll)

        def on_close() -> None:
            try:
                if poll_job["id"] is not None:
                    win.after_cancel(poll_job["id"])
            except Exception:
                pass
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

        bottom = ttk.Frame(main)
        bottom.pack(fill=tk.X, pady=(15, 0))
        ttk.Button(bottom, text="Re-check", command=refresh).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Close", command=on_close).pack(side=tk.RIGHT)

        poll_job["id"] = win.after(1500, poll)

    def show_analytics_dashboard(self):
        """Show the comprehensive analytics dashboard."""
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("Analytics Dashboard - Strava for Writers")
        dashboard_window.geometry("1200x800")
        dashboard_window.transient(self.root)
        
        # Configure grid weights for the window
        dashboard_window.columnconfigure(0, weight=1)
        dashboard_window.rowconfigure(0, weight=1)
        
        # Create dashboard
        dashboard = AnalyticsDashboard(dashboard_window, self.analytics)
        dashboard_frame = dashboard.create_dashboard()
        dashboard_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        # Add close button
        ttk.Button(dashboard_window, text="Close", command=dashboard_window.destroy).grid(row=1, column=0, pady=10)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Word Counter - Strava for Writers",
            "Word Counter v3.0 - Strava for Writers\n\n"
            "A comprehensive word counting application with advanced analytics,\n"
            "goal tracking, and social features for writers.\n\n"
            "Features:\n"
            "• Real-time word counting and WPM tracking\n"
            "• Advanced analytics dashboard with visualizations\n"
            "• Goal setting and progress tracking\n"
            "• Achievement system and gamification\n"
            "• Writing streaks and consistency tracking\n"
            "• Social features and challenges\n"
            "• Allowlist model: only runs in your writing apps\n"
            "• Comprehensive data export and backup"
        )

    def on_close(self):
        """Handle application closure."""
        if self.app_state.recording:
            response = messagebox.askyesnocancel(
                "Save Session?",
                "Recording is in progress. Do you want to save before exiting?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.stop_recording()
        
        # Save window geometry
        self.config.set("window_geometry", self.root.geometry())
        if self._daily_goal_save_job is not None:
            try:
                self.root.after_cancel(self._daily_goal_save_job)
            except (tk.TclError, ValueError):
                pass
            self._daily_goal_save_job = None
        self.data_manager.flush_pending(force=True)
        try:
            if hasattr(self, "focus_watcher") and self.focus_watcher is not None:
                self.focus_watcher.stop()
        except Exception as e:
            self.logger.warning(f"Error stopping focus watcher: {e}")
        self.root.destroy()


class OnboardingWizard:
    """First-run wizard.

    Two screens on Windows (welcome/privacy, then apps + login). Three screens
    on macOS (adds a permissions step between the two) because pynput's
    keyboard listener is a no-op on macOS until the user grants Accessibility
    and Input Monitoring in System Settings.
    """

    def __init__(self, root: tk.Tk, app: "WordCountApp"):
        self.root = root
        self.app = app
        self.completed = False

        self.win = tk.Toplevel(root)
        self.win.title("Welcome to WordCounter")
        self.win.geometry("640x580")
        self.win.resizable(False, False)
        self.win.transient(root)
        self.win.grab_set()

        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() // 2) - (640 // 2)
        y = (self.win.winfo_screenheight() // 2) - (580 // 2)
        self.win.geometry(f"640x580+{x}+{y}")

        self.win.protocol("WM_DELETE_WINDOW", self._on_x_close)

        self.allowed_vars: Dict[str, tk.BooleanVar] = {}
        self.custom_apps: List[str] = []
        self.startup_var = tk.BooleanVar(value=bool(app.config.get("launch_on_startup", False)))

        # Permission-status vars; only used on macOS but safe to create either way.
        self._perm_accessibility_var = tk.StringVar(value="Unknown")
        self._perm_input_monitoring_var = tk.StringVar(value="Unknown")
        self._perm_poll_job: Optional[str] = None

        self.container = ttk.Frame(self.win, padding="24")
        self.container.pack(fill=tk.BOTH, expand=True)

        # Build the step list dynamically: intro -> (permissions?) -> apps/login.
        self._screens: List[Tuple[str, Any]] = [("What this app does", self._render_welcome)]
        if IS_MACOS:
            self._screens.append(("Grant permissions", self._render_mac_permissions))
        self._screens.append(("Pick writing apps", self._render_apps))

        self._show_screen(0)

    # --- screen plumbing --------------------------------------------------

    def _clear(self) -> None:
        if self._perm_poll_job is not None:
            try:
                self.win.after_cancel(self._perm_poll_job)
            except Exception:
                pass
            self._perm_poll_job = None
        for w in self.container.winfo_children():
            w.destroy()

    def _show_screen(self, index: int) -> None:
        if not (0 <= index < len(self._screens)):
            return
        self._clear()
        title, renderer = self._screens[index]
        total = len(self._screens)

        ttk.Label(self.container, text=self._screens[index][0] if index == 0 else title,
                  font=("Helvetica", 18, "bold")).pack(anchor=tk.W, pady=(0, 8))
        if index == 0:
            heading = f"Step 1 of {total} - What this app does"
        else:
            heading = f"Step {index + 1} of {total} - {title}"
        ttk.Label(self.container, text=heading, foreground="#666").pack(
            anchor=tk.W, pady=(0, 16)
        )

        body = ttk.Frame(self.container)
        body.pack(fill=tk.BOTH, expand=True)
        renderer(body)

        self._render_nav(index)

    def _render_nav(self, index: int) -> None:
        btns = ttk.Frame(self.container)
        btns.pack(fill=tk.X, pady=(16, 0))

        if index == 0:
            ttk.Button(btns, text="Cancel", command=self._on_x_close).pack(side=tk.LEFT)
        else:
            ttk.Button(btns, text="< Back", command=lambda: self._show_screen(index - 1)).pack(side=tk.LEFT)

        if index == len(self._screens) - 1:
            ttk.Button(btns, text="Finish", command=self._finish).pack(side=tk.RIGHT)
        else:
            ttk.Button(btns, text="Next >", command=lambda: self._show_screen(index + 1)).pack(side=tk.RIGHT)

    # --- screen renderers -------------------------------------------------

    def _render_welcome(self, parent: ttk.Frame) -> None:
        # Retitle the label we already rendered: the welcome heading above
        # read 'What this app does', so don't re-add one here. Just body text.
        bg = self.win.cget("bg")
        body = tk.Text(parent, wrap=tk.WORD, height=18, relief=tk.FLAT,
                       background=bg, borderwidth=0, font=("Helvetica", 10))
        body.pack(fill=tk.BOTH, expand=True)
        body.insert("1.0",
            "WordCounter tracks your writing productivity by counting words\n"
            "typed in your writing apps (Obsidian, Microsoft Word, Evernote,\n"
            "Scrivener, and so on).\n\n"
            "How this is NOT a keylogger:\n\n"
            "  - A foreground-app hook watches which app is focused.\n"
            "  - The keyboard listener is only created while one of your\n"
            "    allowlisted writing apps is focused. When you switch to\n"
            "    anything else (Chrome, Slack, your password manager, the\n"
            "    terminal), the listener is stopped and this process\n"
            "    receives zero keystrokes.\n\n"
            "  - Only aggregate counts (words, duration, WPM) are stored.\n"
            "    The typed word you are in the middle of stays in RAM only\n"
            "    until the next word boundary, then is discarded.\n\n"
            "  - No cloud uploads, no telemetry, no network calls.\n\n"
            "You can change your writing-app list any time from Tools >\n"
            "Writing Apps.\n"
        )
        body.config(state=tk.DISABLED)

    def _render_mac_permissions(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=(
                "macOS protects keyboard access with two permission prompts. "
                "WordCounter needs BOTH to count words."
            ),
            wraplength=580, justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        bullets = tk.Text(parent, wrap=tk.WORD, height=8, relief=tk.FLAT,
                          background=self.win.cget("bg"), borderwidth=0,
                          font=("Helvetica", 10))
        bullets.pack(fill=tk.X, pady=(0, 12))
        bullets.insert("1.0",
            "  - Accessibility: lets WordCounter notice WHICH app is focused so\n"
            "    it can stop listening outside your writing apps.\n\n"
            "  - Input Monitoring: lets WordCounter observe individual key\n"
            "    presses inside your writing apps, to count words.\n\n"
            "Click each button below to open the right pane in System Settings,\n"
            "then toggle WordCounter on. You may need to quit + reopen\n"
            "WordCounter after granting Input Monitoring.\n"
        )
        bullets.config(state=tk.DISABLED)

        grid = ttk.Frame(parent)
        grid.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(grid, text="Accessibility:", width=18, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Label(grid, textvariable=self._perm_accessibility_var, width=14).grid(row=0, column=1, sticky=tk.W, padx=(4, 12))
        ttk.Button(grid, text="Open Settings",
                   command=lambda: open_mac_privacy_pane("accessibility")).grid(row=0, column=2, sticky=tk.W)

        ttk.Label(grid, text="Input Monitoring:", width=18, anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Label(grid, textvariable=self._perm_input_monitoring_var, width=14).grid(row=1, column=1, sticky=tk.W, padx=(4, 12))
        ttk.Button(grid, text="Open Settings",
                   command=lambda: open_mac_privacy_pane("input_monitoring")).grid(row=1, column=2, sticky=tk.W)

        ttk.Button(parent, text="Re-check now", command=self._refresh_mac_permissions).pack(
            anchor=tk.W, pady=(8, 0)
        )

        ttk.Label(
            parent,
            text=(
                "You can continue without granting these, but WordCounter "
                "will record zero words until you do. You can re-open this "
                "wizard later from the Tools menu."
            ),
            wraplength=580, justify=tk.LEFT, foreground="#666",
        ).pack(anchor=tk.W, pady=(12, 0))

        self._refresh_mac_permissions()
        self._schedule_perm_poll()

    def _refresh_mac_permissions(self) -> None:
        def label(value: Optional[bool]) -> str:
            if value is True:
                return "Granted"
            if value is False:
                return "Not granted"
            return "Unknown"
        self._perm_accessibility_var.set(label(mac_accessibility_granted()))
        self._perm_input_monitoring_var.set(label(mac_input_monitoring_granted()))

    def _schedule_perm_poll(self) -> None:
        self._perm_poll_job = self.win.after(1500, self._poll_permissions_tick)

    def _poll_permissions_tick(self) -> None:
        self._refresh_mac_permissions()
        self._schedule_perm_poll()

    def _render_apps(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="The keyboard listener will only run while one of these is focused.",
            wraplength=580, justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        list_frame = ttk.LabelFrame(parent, text="Default writing apps", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        inner = ttk.Frame(list_frame)
        inner.pack(fill=tk.BOTH, expand=True)

        existing = {a.lower() for a in self.app.app_focus_manager.get_allowed_apps()}
        defaults = Config.DEFAULT_ALLOWED_APPS

        col_a = ttk.Frame(inner)
        col_a.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        col_b = ttk.Frame(inner)
        col_b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        half = (len(defaults) + 1) // 2
        for i, app_name in enumerate(defaults):
            var = tk.BooleanVar(value=(app_name.lower() in existing) if existing else True)
            self.allowed_vars[app_name] = var
            parent_col = col_a if i < half else col_b
            ttk.Checkbutton(parent_col, text=friendly_app_name(app_name),
                            variable=var).pack(anchor=tk.W, pady=2)

        custom_frame = ttk.LabelFrame(parent, text="Additional apps", padding="10")
        custom_frame.pack(fill=tk.X, pady=(12, 0))

        custom_row = ttk.Frame(custom_frame)
        custom_row.pack(fill=tk.X)
        self.custom_listbox = tk.Listbox(custom_row, height=3)
        self.custom_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        custom_buttons = ttk.Frame(custom_row)
        custom_buttons.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(custom_buttons, text="Add...", command=self._add_custom, width=12).pack(pady=(0, 4))
        ttk.Button(custom_buttons, text="Remove", command=self._remove_custom, width=12).pack()

        for extra in sorted(existing - {d.lower() for d in defaults}):
            self.custom_apps.append(extra)
            self.custom_listbox.insert(tk.END, friendly_app_name(extra))

        startup_label = (
            "Launch WordCounter at login" if IS_MACOS
            else "Launch WordCounter when I sign in to Windows"
        )
        ttk.Checkbutton(parent, text=startup_label, variable=self.startup_var).pack(
            anchor=tk.W, pady=(16, 0)
        )

    # --- actions ---------------------------------------------------------

    def _add_custom(self) -> None:
        prompt = (
            "Enter the app name (as shown in the Dock, e.g. 'Ulysses'):"
            if IS_MACOS
            else "Enter the executable name (e.g., joplin.exe):"
        )
        name = simpledialog.askstring("Add writing app", prompt, parent=self.win)
        if not name:
            return
        name = name.strip().lower()
        if IS_WINDOWS and name and not name.endswith(".exe"):
            name = name + ".exe"
        if name and name not in self.custom_apps:
            self.custom_apps.append(name)
            self.custom_listbox.insert(tk.END, friendly_app_name(name))

    def _remove_custom(self) -> None:
        sel = self.custom_listbox.curselection()
        if sel:
            idx = sel[0]
            if 0 <= idx < len(self.custom_apps):
                self.custom_apps.pop(idx)
            self.custom_listbox.delete(idx)

    def _finish(self) -> None:
        selected = [name for name, var in self.allowed_vars.items() if var.get()]
        selected += list(self.custom_apps)
        if not selected:
            if not messagebox.askyesno(
                "Empty allowlist",
                "You haven't selected any writing apps. WordCounter won't track anything. Continue anyway?",
                parent=self.win,
            ):
                return

        self.app.app_focus_manager.set_allowed_apps(selected)

        want_startup = bool(self.startup_var.get())
        ok = set_launch_on_startup(want_startup)
        if not ok:
            auto_msg = (
                "Could not update the login item. You can try again later from the Tools menu."
                if IS_MACOS
                else "Could not update the Windows startup entry. You can try again later from the Tools menu."
            )
            messagebox.showwarning("Startup setting", auto_msg, parent=self.win)
        self.app.config.set("launch_on_startup", want_startup)
        self.app.config.set("onboarding_completed", True)
        self.completed = True
        self._clear()  # also cancels the permissions poll
        self.win.destroy()

    def _on_x_close(self) -> None:
        if messagebox.askyesno(
            "Skip setup?",
            "Skip the wizard and use the default writing-app list?\nYou can always adjust it from Tools > Writing Apps.",
            parent=self.win,
        ):
            self.app.config.set("onboarding_completed", True)
            self.completed = True
            self._clear()
            self.win.destroy()


def main():
    """Main entry point for the application."""
    install_crash_handlers()
    try:
        root = tk.Tk()
        app = WordCountApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        log_path = write_crash_log(type(e), e, e.__traceback__)
        try:
            msg = f"Failed to start application: {e}"
            if log_path is not None:
                msg += f"\n\nA crash log was saved to:\n{log_path}"
            messagebox.showerror("Critical Error", msg)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()