import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pynput import keyboard
from pynput.keyboard import Key
import threading
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from collections import deque
import time
from dataclasses import dataclass, field
from pathlib import Path
import sys
from contextlib import contextmanager
import psutil
import win32gui
import win32process

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

class SecurityManager:
    """Manages security features to prevent logging sensitive data."""
    
    def __init__(self):
        # Applications where word counting should be paused
        self.excluded_apps = {
            "chrome.exe", "firefox.exe", "edge.exe", "safari.exe",  # Browsers
            "outlook.exe", "thunderbird.exe", "mail.exe",  # Email clients
            "teams.exe", "slack.exe", "discord.exe", "zoom.exe",  # Communication apps
            "putty.exe", "mobaxterm.exe", "securecrt.exe",  # SSH clients
            "vpn.exe", "openvpn.exe", "nordvpn.exe",  # VPN clients
            "keepass.exe", "1password.exe", "lastpass.exe", "bitwarden.exe",  # Password managers
            "cmd.exe", "powershell.exe", "terminal.exe",  # Command line
            "rdp.exe", "mstsc.exe",  # Remote desktop
            # Crypto wallets and financial applications
            "metamask.exe", "phantom.exe", "trezor.exe", "coinbase.exe", "rabby.exe", "ledger.exe",
            "exodus.exe", "atomic.exe", "trust.exe", "binance.exe", "kraken.exe", "gemini.exe",
            "coinomi.exe", "jaxx.exe", "electrum.exe", "bitcoin-qt.exe", "litecoin-qt.exe",
            "ethereum-wallet.exe", "myetherwallet.exe", "uniswap.exe", "pancakeswap.exe",
            "opensea.exe", "nft.exe", "defi.exe", "wallet.exe", "crypto.exe", "blockchain.exe",
            "brave.exe", "opera.exe",  # Browsers with built-in crypto wallets
        }
        
        # Window titles containing sensitive keywords
        self.sensitive_keywords = {
            "password", "login", "sign in", "authentication", "security",
            "credit card", "ssn", "social security", "bank", "account",
            "private", "confidential", "secret", "secure",
            # Crypto and financial keywords
            "wallet", "crypto", "bitcoin", "ethereum", "blockchain", "defi", "nft",
            "private key", "seed phrase", "mnemonic", "recovery", "backup",
            "metamask", "phantom", "trezor", "ledger", "coinbase", "binance",
            "exchange", "trading", "portfolio", "balance", "transaction",
            "swap", "stake", "yield", "liquidity", "token", "coin"
        }
        
        self.security_enabled = True
        self.current_app = None
        self.current_window_title = None
    
    def get_active_window_info(self) -> Tuple[str, str]:
        """Get the current active window's process name and title."""
        try:
            # Get the foreground window
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process name
            process = psutil.Process(pid)
            process_name = process.name().lower()
            
            return process_name, window_title.lower()
        except Exception:
            return "", ""
    
    def is_sensitive_context(self) -> bool:
        """Check if current context is sensitive and should be excluded."""
        if not self.security_enabled:
            return False
        
        try:
            process_name, window_title = self.get_active_window_info()
            
            # Check if process is in excluded list
            if process_name in self.excluded_apps:
                return True
            
            # Check if window title contains sensitive keywords
            for keyword in self.sensitive_keywords:
                if keyword in window_title:
                    return True
            
            return False
            
        except Exception:
            # If we can't determine context, err on the side of caution
            return True
    
    def update_context(self) -> None:
        """Update current application context."""
        self.current_app, self.current_window_title = self.get_active_window_info()
    
    def set_security_enabled(self, enabled: bool) -> None:
        """Enable or disable security features."""
        self.security_enabled = enabled
    
    def add_excluded_app(self, app_name: str) -> None:
        """Add an application to the exclusion list."""
        self.excluded_apps.add(app_name.lower())
    
    def remove_excluded_app(self, app_name: str) -> None:
        """Remove an application from the exclusion list."""
        self.excluded_apps.discard(app_name.lower())
    
    def get_excluded_apps(self) -> set:
        """Get the current list of excluded applications."""
        return self.excluded_apps.copy()

@dataclass
class SessionData:
    """Data class for session information."""
    word_count: int = 0
    start_time: Optional[datetime] = None
    duration: int = 0
    wpm: float = 0.0
    words_per_minute_history: List[float] = field(default_factory=list)
    
    def reset(self) -> None:
        """Reset session data."""
        self.word_count = 0
        self.start_time = None
        self.duration = 0
        self.wpm = 0.0
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
    DEFAULT_CONFIG = {
        "auto_save_interval": 300,  # seconds
        "daily_goal": 1000,
        "theme": "clam",
        "window_geometry": "700x500",
        "show_notifications": True,
        "backup_enabled": True,
        "max_backup_files": 5,
        "min_word_length": 2,
        "wpm_history_size": 10
    }
    
    def __init__(self, config_file: str = "config.json"):
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
    
    def __init__(self, min_word_length: int = 2):
        self.current_word = ""
        self.min_word_length = min_word_length
        self.word_pattern = re.compile(r'\b\w+\b')
        self.word_count_cache = {}  # Cache for word validation
        
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
        """Check if current text forms a valid word with improved validation."""
        word = self.current_word.strip()
        self.current_word = ""
        
        if not word:
            return 0
        
        # Check cache first
        if word in self.word_count_cache:
            return self.word_count_cache[word]
        
        # Validate word
        is_valid = self._is_valid_word(word)
        word_count = 1 if is_valid else 0
        
        # Cache result for performance
        self.word_count_cache[word] = word_count
        
        # Limit cache size to prevent memory issues
        if len(self.word_count_cache) > 1000:
            self.word_count_cache.clear()
        
        return word_count
    
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
        common_abbrevs = {
            "I", "a", "an", "Mr", "Mrs", "Dr", "Prof", "etc", "vs", "etc",
            "i.e", "e.g", "a.m", "p.m", "A.M", "P.M"
        }
        return word.lower() in {abbrev.lower() for abbrev in common_abbrevs}
    
    def reset(self) -> None:
        """Reset the detector state."""
        self.current_word = ""
        self.word_count_cache.clear()


class Statistics:
    """Manages word count statistics and metrics with improved performance."""
    
    def __init__(self, wpm_history_size: int = 10):
        self.session_data = SessionData()
        self.wpm_history_size = wpm_history_size
        self._last_update_time = 0
        self._update_interval = 0.1  # Update WPM every 100ms for better accuracy
        
    def start_session(self) -> None:
        """Start a new counting session."""
        self.session_data.reset()
        self.session_data.start_time = datetime.now()
        self._last_update_time = time.time()
        
    def add_word(self) -> None:
        """Record a new word with improved WPM calculation."""
        self.session_data.word_count += 1
        current_time = time.time()
        
        # Update WPM more frequently for better accuracy
        if current_time - self._last_update_time >= self._update_interval:
            self._update_wpm(current_time)
            self._last_update_time = current_time
    
    def _update_wpm(self, current_time: float) -> None:
        """Update WPM calculation with improved algorithm."""
        if not self.session_data.start_time:
            return
            
        duration_minutes = (current_time - self.session_data.start_time.timestamp()) / 60.0
        if duration_minutes > 0:
            overall_wpm = self.session_data.word_count / duration_minutes
            
            # Add to history for rolling average
            self.session_data.words_per_minute_history.append(overall_wpm)
            
            # Keep only the most recent entries
            if len(self.session_data.words_per_minute_history) > self.wpm_history_size:
                self.session_data.words_per_minute_history = self.session_data.words_per_minute_history[-self.wpm_history_size:]
            
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
    
    def __init__(self, data_file: str = "WordCountData.xlsx"):
        self.data_file = Path(data_file)
        self.backup_dir = self.data_file.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def save_session(self, session_data: SessionData) -> bool:
        """Save session data with error handling and backup."""
        try:
            new_data = pd.DataFrame({
                'Date and Time': [session_data.start_time],
                'Word Count': [session_data.word_count],
                'Duration (seconds)': [session_data.duration],
                'WPM': [session_data.wpm],
                'Productivity Score': [session_data.words_per_minute_history[-1] if session_data.words_per_minute_history else 0.0]
            })
            
            # Create backup before modifying
            self._create_backup()
            
            if self.data_file.exists():
                existing_data = pd.read_excel(self.data_file)
                df = pd.concat([existing_data, new_data], ignore_index=True)
            else:
                df = new_data
            
            # Ensure data directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_excel(self.data_file, index=False)
            return True
            
        except Exception as e:
            logging.error(f"Error saving session data: {e}")
            return False
    
    def load_today_data(self) -> int:
        """Load today's word count from saved data."""
        try:
            if not self.data_file.exists():
                return 0
                
            df = pd.read_excel(self.data_file)
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
            if not self.data_file.exists():
                return {}
                
            df = pd.read_excel(self.data_file)
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
            if not self.data_file.exists():
                return None
                
            df = pd.read_excel(self.data_file)
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
    
    def _create_backup(self) -> None:
        """Create a backup of the data file."""
        try:
            if self.data_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"data_backup_{timestamp}.xlsx"
                
                import shutil
                shutil.copy2(self.data_file, backup_file)
                
                # Clean up old backups (keep last 10)
                self._cleanup_old_backups()
                
        except Exception as e:
            logging.warning(f"Failed to create data backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = sorted(self.backup_dir.glob("data_backup_*.xlsx"))
            if len(backup_files) > 10:
                for old_backup in backup_files[:-10]:
                    old_backup.unlink()
                    
        except Exception as e:
            logging.warning(f"Failed to cleanup old backups: {e}")


class WordCountApp:
    def __init__(self, root: tk.Tk):
        """Initialize the WordCountApp with improved UI and functionality."""
        self.setup_logging()
        self.root = root
        self.config = Config()
        self.data_manager = DataManager()
        self.word_detector = WordDetector(self.config.get("min_word_length", 2))
        self.statistics = Statistics(self.config.get("wpm_history_size", 10))
        self.app_state = AppState()
        self.keyboard_shortcuts = KeyboardShortcuts(self)
        self.security_manager = SecurityManager()
        
        self.configure_root()
        self.initialize_variables()
        self.create_ui()
        self.load_data()
        self.setup_auto_save()
        self.update_display_timer()
        self.keyboard_shortcuts.bind_shortcuts()

    def setup_logging(self) -> None:
        """Configure logging for the application."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('word_counter.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def configure_root(self) -> None:
        """Configure the root window properties."""
        self.root.title("Word Counter Pro")
        self.root.geometry(self.config.get("window_geometry"))
        self.root.minsize(600, 400)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use(self.config.get("theme"))
        
        # Custom styles
        self.style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
        self.style.configure("Stats.TLabel", font=("Helvetica", 11))
        self.style.configure("Success.TLabel", foreground="green")
        self.style.configure("Warning.TLabel", foreground="orange")

    def initialize_variables(self) -> None:
        """Initialize instance variables."""
        self.listener: Optional[keyboard.Listener] = None
        self.today_total = 0
        self.daily_goal = self.config.get("daily_goal", 1000)
        self.last_notification_time = 0
        self.notification_cooldown = 5  # seconds between notifications

    def create_ui(self) -> None:
        """Create the user interface with improved layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Word Counter Pro", style="Title.TLabel")
        title_label.grid(row=0, column=0, pady=(0, 10))
        
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
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        stats_frame.columnconfigure(1, weight=1)
        
        # Current Session
        ttk.Label(stats_frame, text="Current Session:", style="Stats.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10)
        )
        self.session_count_label = ttk.Label(stats_frame, text="0 words", style="Stats.TLabel")
        self.session_count_label.grid(row=0, column=1, sticky=tk.W)
        
        # Today's Total
        ttk.Label(stats_frame, text="Today's Total:", style="Stats.TLabel").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10)
        )
        self.today_count_label = ttk.Label(stats_frame, text="0 words", style="Stats.TLabel")
        self.today_count_label.grid(row=1, column=1, sticky=tk.W)
        
        # WPM
        ttk.Label(stats_frame, text="Words/Minute:", style="Stats.TLabel").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 10)
        )
        self.wpm_label = ttk.Label(stats_frame, text="0 WPM", style="Stats.TLabel")
        self.wpm_label.grid(row=2, column=1, sticky=tk.W)
        
        # Session Duration
        ttk.Label(stats_frame, text="Session Time:", style="Stats.TLabel").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 10)
        )
        self.duration_label = ttk.Label(stats_frame, text="00:00:00", style="Stats.TLabel")
        self.duration_label.grid(row=3, column=1, sticky=tk.W)

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
        control_frame.grid(row=3, column=0, pady=20)
        
        # Start Button
        self.start_button = ttk.Button(
            control_frame,
            text="▶ Start Recording",
            command=self.start_recording,
            width=20
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        # Pause Button
        self.pause_button = ttk.Button(
            control_frame,
            text="⏸ Pause",
            command=self.toggle_pause,
            state=tk.DISABLED,
            width=20
        )
        self.pause_button.grid(row=0, column=1, padx=5)
        
        # Stop Button
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹ Stop",
            command=self.stop_recording,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.grid(row=0, column=2, padx=5)

    def create_status_bar(self, parent):
        """Create the status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            parent,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

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
        view_menu.add_command(label="Statistics", command=self.show_statistics)
        view_menu.add_command(label="History", command=self.show_history)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Security Settings", command=self.show_security_settings)
        tools_menu.add_separator()
        tools_menu.add_command(label="Keyboard Shortcuts", command=self.keyboard_shortcuts.show_shortcuts_help)
        tools_menu.add_separator()
        tools_menu.add_command(label="Backup Data", command=self.backup_data)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
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
        if self.app_state.recording and not self.app_state.paused:
            self.update_display()
        self.root.after(1000, self.update_display_timer)

    def on_key_press(self, key):
        """Handle keyboard input with security checks."""
        if self.app_state.recording and not self.app_state.paused:
            # Check if we're in a sensitive context
            if self.security_manager.is_sensitive_context():
                # Don't process keystrokes in sensitive contexts
                return
            
            word_count = self.word_detector.process_key(key)
            if word_count:
                self.statistics.add_word()
                self.update_display()
    
    def _show_goal_achievement_notification(self):
        """Show notification when daily goal is achieved."""
        current_time = time.time()
        if (self.config.get("show_notifications", True) and 
            current_time - self.last_notification_time > self.notification_cooldown):
            
            self.last_notification_time = current_time
            messagebox.showinfo(
                "Goal Achieved! 🎉",
                f"Congratulations! You've reached your daily goal of {self.daily_goal} words!"
            )

    def start_recording(self):
        """Start the recording session."""
        try:
            # Initialize statistics
            self.statistics.start_session()
            
            # Start keyboard listener
            self.listener = keyboard.Listener(on_press=self.on_key_press)
            self.listener.start()
            
            # Update state
            self.app_state.recording = True
            self.app_state.paused = False
            self.update_button_states()
            self.status_var.set("Recording...")
            
            self.logger.info("Recording started")
            
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            messagebox.showerror("Error", "Failed to start recording")

    def toggle_pause(self):
        """Toggle pause state."""
        self.app_state.paused = not self.app_state.paused
        self.pause_button.config(text="▶ Resume" if self.app_state.paused else "⏸ Pause")
        self.status_var.set("Paused" if self.app_state.paused else "Recording...")
        self.logger.info(f"Recording {'paused' if self.app_state.paused else 'resumed'}")

    def stop_recording(self):
        """Stop the recording session."""
        try:
            # Stop listener
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            # Save session if there are words
            session_data = self.statistics.get_session_data()
            if session_data.word_count > 0:
                # Update session duration before saving
                session_data.duration = self.statistics.get_session_duration()
                if self.data_manager.save_session(session_data):
                    self.today_total += session_data.word_count
                    self.logger.info(f"Session saved: {session_data.word_count} words")
                else:
                    messagebox.showwarning("Warning", "Failed to save session data")
            
            # Reset
            self.app_state.recording = False
            self.app_state.paused = False
            self.statistics.reset()
            self.word_detector.reset()
            
            self.update_button_states()
            self.update_display()
            self.status_var.set("Ready")
            
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
                    self.status_var.set("Auto-saved")
                    self.root.after(2000, lambda: self.status_var.set("Recording..."))
                    self.logger.info("Auto-save completed")
                else:
                    self.logger.warning("Auto-save failed")
            
            interval = self.config.get("auto_save_interval", 300) * 1000
            self.root.after(interval, auto_save)
        
        interval = self.config.get("auto_save_interval", 300) * 1000
        self.root.after(interval, auto_save)

    def update_daily_goal(self):
        """Update the daily goal setting."""
        try:
            self.daily_goal = int(self.goal_var.get())
            self.config.set("daily_goal", self.daily_goal)
            self.update_display()
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
                self.data_manager._create_backup()
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
            if self.data_manager.data_file.exists():
                df = pd.read_excel(self.data_manager.data_file)
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

    def show_security_settings(self):
        """Show security settings dialog."""
        security_window = tk.Toplevel(self.root)
        security_window.title("Security Settings")
        security_window.geometry("600x500")
        security_window.resizable(False, False)
        security_window.transient(self.root)
        security_window.grab_set()
        
        # Center the window
        security_window.update_idletasks()
        x = (security_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (security_window.winfo_screenheight() // 2) - (500 // 2)
        security_window.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(security_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Security enabled checkbox
        security_enabled_var = tk.BooleanVar(value=self.security_manager.security_enabled)
        security_checkbox = ttk.Checkbutton(
            main_frame,
            text="Enable Security Features",
            variable=security_enabled_var,
            command=lambda: self.security_manager.set_security_enabled(security_enabled_var.get())
        )
        security_checkbox.pack(anchor=tk.W, pady=(0, 20))
        
        # Excluded applications frame
        excluded_frame = ttk.LabelFrame(main_frame, text="Excluded Applications", padding="10")
        excluded_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # List of excluded apps
        excluded_listbox = tk.Listbox(excluded_frame, height=8)
        excluded_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(excluded_frame, orient=tk.VERTICAL, command=excluded_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        excluded_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(excluded_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def add_excluded_app():
            app_name = tk.simpledialog.askstring("Add Application", "Enter application name (e.g., chrome.exe):")
            if app_name:
                self.security_manager.add_excluded_app(app_name)
                refresh_excluded_list()
        
        def remove_excluded_app():
            selection = excluded_listbox.curselection()
            if selection:
                app_name = excluded_listbox.get(selection[0])
                self.security_manager.remove_excluded_app(app_name)
                refresh_excluded_list()
        
        def refresh_excluded_list():
            excluded_listbox.delete(0, tk.END)
            for app in sorted(self.security_manager.get_excluded_apps()):
                excluded_listbox.insert(tk.END, app)
        
        ttk.Button(buttons_frame, text="Add Application", command=add_excluded_app).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Remove Selected", command=remove_excluded_app).pack(side=tk.LEFT)
        
        # Sensitive keywords frame
        keywords_frame = ttk.LabelFrame(main_frame, text="Sensitive Keywords", padding="10")
        keywords_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        keywords_text = tk.Text(keywords_frame, height=4, wrap=tk.WORD)
        keywords_text.pack(fill=tk.BOTH, expand=True)
        
        # Load current keywords
        keywords_text.insert(tk.END, ", ".join(self.security_manager.sensitive_keywords))
        
        def save_keywords():
            keywords_text_content = keywords_text.get(1.0, tk.END).strip()
            if keywords_text_content:
                keywords = {kw.strip().lower() for kw in keywords_text_content.split(",")}
                self.security_manager.sensitive_keywords = keywords
        
        # Current context frame
        context_frame = ttk.LabelFrame(main_frame, text="Current Context", padding="10")
        context_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.context_label = ttk.Label(context_frame, text="Click 'Update' to see current application context")
        self.context_label.pack(anchor=tk.W)
        
        def update_context():
            self.security_manager.update_context()
            app_name = self.security_manager.current_app or "Unknown"
            window_title = self.security_manager.current_window_title or "Unknown"
            is_sensitive = self.security_manager.is_sensitive_context()
            
            context_text = f"Application: {app_name}\nWindow: {window_title}\nSensitive: {'Yes' if is_sensitive else 'No'}"
            self.context_label.config(text=context_text)
        
        ttk.Button(context_frame, text="Update Context", command=update_context).pack(anchor=tk.W, pady=(5, 0))
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_settings():
            save_keywords()
            messagebox.showinfo("Success", "Security settings saved!")
        
        def close_dialog():
            save_settings()
            security_window.destroy()
        
        ttk.Button(bottom_frame, text="Save", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_frame, text="Cancel", command=security_window.destroy).pack(side=tk.RIGHT)
        
        # Initialize the excluded apps list
        refresh_excluded_list()
        
        # Update context initially
        update_context()

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Word Counter Pro",
            "Word Counter Pro v2.0\n\n"
            "A professional word counting application\n"
            "with real-time tracking and statistics.\n\n"
            "Features:\n"
            "• Real-time word counting\n"
            "• Daily goal tracking\n"
            "• Writing statistics\n"
            "• Session history\n"
            "• Auto-save functionality\n"
            "• Security features to protect sensitive data"
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
        self.root.destroy()


def main():
    """Main entry point for the application."""
    try:
        root = tk.Tk()
        app = WordCountApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        messagebox.showerror("Critical Error", f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()