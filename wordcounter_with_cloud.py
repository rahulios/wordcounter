"""
Word Counter Pro with Cloud Sync Integration
This is a modified version of the main WordCounter app that includes cloud sync functionality
"""

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
import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from calendar import monthrange
import seaborn as sns

# Import cloud sync modules
from cloud_sync import cloud_sync_manager
from cloud_integration import CloudIntegration
from auth_ui import LoginDialog, RegisterDialog, AccountManagerDialog, SyncStatusWidget

# Import all the existing classes from the original file
# (In a real implementation, you'd import these from separate modules)
from wordcounter_09_06_25 import (
    WordCounterError, ConfigurationError, DataError,
    WritingSession, WritingGoal, Achievement, WritingStreak, WritingInsights,
    AdvancedAnalytics, GoalManager, SecurityManager, SessionData, AppState,
    KeyboardShortcuts, Config, WordDetector, Statistics, DataManager,
    AnalyticsDashboard, SocialFeatures, WordCountApp
)

class WordCountAppWithCloud(WordCountApp):
    """Enhanced WordCounter app with cloud sync functionality"""
    
    def __init__(self, root: tk.Tk):
        """Initialize the enhanced WordCountApp with cloud sync"""
        # Initialize cloud integration first
        self.cloud_integration = CloudIntegration(self)
        
        # Call parent constructor
        super().__init__(root)
        
        # Add cloud sync features
        self._setup_cloud_features()
        
    def _setup_cloud_features(self):
        """Setup cloud sync features"""
        # Update window title
        self.root.title("Word Counter Pro - Cloud Sync")
        
        # Add cloud sync status widget
        self._add_cloud_sync_widget()
        
        # Update menu bar with cloud features
        self._update_menu_with_cloud_features()
        
        # Start auto-sync if user is logged in
        if self.cloud_integration.is_user_logged_in():
            self.cloud_integration.start_auto_sync()
    
    def _add_cloud_sync_widget(self):
        """Add cloud sync status widget to the main window"""
        # Add sync status to the status bar area
        sync_frame = ttk.Frame(self.root)
        sync_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Create sync widget
        self.sync_widget = SyncStatusWidget(sync_frame)
        self.sync_widget.create_widget(sync_frame)
        
        # Add manual sync button
        ttk.Button(sync_frame, text="Manual Sync", 
                  command=self.cloud_integration.manual_sync).pack(side=tk.RIGHT, padx=(5, 0))
    
    def _update_menu_with_cloud_features(self):
        """Update menu bar with cloud sync features"""
        # Get the existing menubar
        menubar = self.root.native_menu if hasattr(self.root, 'native_menu') else None
        if not menubar:
            # Create new menubar if it doesn't exist
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)
        
        # Add Account menu
        account_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Account", menu=account_menu)
        
        if self.cloud_integration.is_user_logged_in():
            # User is logged in
            user_profile = self.cloud_integration.get_user_profile()
            account_menu.add_command(
                label=f"Logged in as {user_profile.username}",
                state=tk.DISABLED
            )
            account_menu.add_separator()
            account_menu.add_command(
                label="Account Management",
                command=self.cloud_integration.show_account_manager
            )
            account_menu.add_command(
                label="Sync Now",
                command=self.cloud_integration.manual_sync
            )
            account_menu.add_separator()
            account_menu.add_command(
                label="Logout",
                command=self._handle_logout
            )
        else:
            # User is not logged in
            account_menu.add_command(
                label="Login",
                command=self.cloud_integration.show_login_dialog
            )
            account_menu.add_command(
                label="Register",
                command=self.cloud_integration.show_register_dialog
            )
        
        # Add Cloud menu
        cloud_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Cloud", menu=cloud_menu)
        cloud_menu.add_command(
            label="Sync Status",
            command=self._show_sync_status
        )
        cloud_menu.add_command(
            label="Sync Settings",
            command=self._show_sync_settings
        )
        cloud_menu.add_separator()
        cloud_menu.add_command(
            label="Cloud Backup",
            command=self._cloud_backup
        )
        cloud_menu.add_command(
            label="Restore from Cloud",
            command=self._restore_from_cloud
        )
    
    def _handle_logout(self):
        """Handle user logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.cloud_integration.logout_user()
            self._update_menu_with_cloud_features()
            if self.sync_widget:
                self.sync_widget.update_status()
            messagebox.showinfo("Logged Out", "You have been logged out successfully")
    
    def _show_sync_status(self):
        """Show detailed sync status dialog"""
        if not self.cloud_integration.is_user_logged_in():
            messagebox.showwarning("Not Logged In", "Please log in to view sync status")
            return
        
        status_window = tk.Toplevel(self.root)
        status_window.title("Sync Status")
        status_window.geometry("400x300")
        status_window.transient(self.root)
        
        # Center the window
        status_window.update_idletasks()
        x = (status_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (status_window.winfo_screenheight() // 2) - (300 // 2)
        status_window.geometry(f"400x300+{x}+{y}")
        
        main_frame = ttk.Frame(status_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Cloud Sync Status", 
                 font=("Helvetica", 16, "bold")).pack(pady=(0, 20))
        
        # Get sync status
        sync_status = cloud_sync_manager.get_sync_status()
        
        # Status information
        info_frame = ttk.LabelFrame(main_frame, text="Status Information", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Online status
        status_text = "Online" if sync_status["is_online"] else "Offline"
        status_color = "green" if sync_status["is_online"] else "red"
        ttk.Label(info_frame, text="Connection:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=status_text, font=("Helvetica", 10, "bold"), 
                 foreground=status_color).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Last sync
        last_sync_text = "Never" if not sync_status["last_sync"] else sync_status["last_sync"]
        ttk.Label(info_frame, text="Last Sync:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=last_sync_text, font=("Helvetica", 10, "bold")).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Sync in progress
        sync_progress_text = "Yes" if sync_status["sync_in_progress"] else "No"
        ttk.Label(info_frame, text="Syncing:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=sync_progress_text, font=("Helvetica", 10, "bold")).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Subscription tier
        ttk.Label(info_frame, text="Subscription:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=sync_status["subscription_tier"].title(), 
                 font=("Helvetica", 10, "bold"), foreground="blue").grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(buttons_frame, text="Sync Now", 
                  command=self.cloud_integration.manual_sync).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Close", 
                  command=status_window.destroy).pack(side=tk.RIGHT)
    
    def _show_sync_settings(self):
        """Show sync settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Sync Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        
        # Center the window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (300 // 2)
        settings_window.geometry(f"400x300+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Sync Settings", 
                 font=("Helvetica", 16, "bold")).pack(pady=(0, 20))
        
        # Auto-sync settings
        auto_sync_frame = ttk.LabelFrame(main_frame, text="Auto Sync", padding="15")
        auto_sync_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.auto_sync_var = tk.BooleanVar(value=self.cloud_integration.auto_sync_enabled)
        ttk.Checkbutton(auto_sync_frame, text="Enable automatic syncing", 
                       variable=self.auto_sync_var,
                       command=self._toggle_auto_sync).pack(anchor=tk.W)
        
        # Sync interval
        ttk.Label(auto_sync_frame, text="Sync Interval (minutes):").pack(anchor=tk.W, pady=(10, 5))
        self.sync_interval_var = tk.StringVar(value=str(self.cloud_integration.sync_interval // 60))
        sync_interval_entry = ttk.Entry(auto_sync_frame, textvariable=self.sync_interval_var, width=10)
        sync_interval_entry.pack(anchor=tk.W)
        
        # Data settings
        data_frame = ttk.LabelFrame(main_frame, text="Data Settings", padding="15")
        data_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.sync_sessions_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(data_frame, text="Sync writing sessions", 
                       variable=self.sync_sessions_var).pack(anchor=tk.W)
        
        self.sync_goals_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(data_frame, text="Sync goals and achievements", 
                       variable=self.sync_goals_var).pack(anchor=tk.W)
        
        self.sync_settings_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(data_frame, text="Sync application settings", 
                       variable=self.sync_settings_var).pack(anchor=tk.W)
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(buttons_frame, text="Save", 
                  command=self._save_sync_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Cancel", 
                  command=settings_window.destroy).pack(side=tk.RIGHT)
    
    def _toggle_auto_sync(self):
        """Toggle auto-sync on/off"""
        if self.auto_sync_var.get():
            self.cloud_integration.start_auto_sync()
        else:
            self.cloud_integration.stop_auto_sync()
    
    def _save_sync_settings(self):
        """Save sync settings"""
        try:
            # Update sync interval
            interval_minutes = int(self.sync_interval_var.get())
            self.cloud_integration.sync_interval = interval_minutes * 60
            
            # Save settings to config
            self.config.set("auto_sync_enabled", self.auto_sync_var.get())
            self.config.set("sync_interval_minutes", interval_minutes)
            self.config.set("sync_sessions", self.sync_sessions_var.get())
            self.config.set("sync_goals", self.sync_goals_var.get())
            self.config.set("sync_settings", self.sync_settings_var.get())
            
            messagebox.showinfo("Settings Saved", "Sync settings have been saved successfully")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for sync interval")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def _cloud_backup(self):
        """Create cloud backup"""
        if not self.cloud_integration.is_user_logged_in():
            messagebox.showwarning("Not Logged In", "Please log in to create cloud backup")
            return
        
        if messagebox.askyesno("Cloud Backup", "Create a backup of your data in the cloud?"):
            success = self.cloud_integration.sync_data_to_cloud(force=True)
            if success:
                messagebox.showinfo("Backup Complete", "Your data has been backed up to the cloud")
            else:
                messagebox.showerror("Backup Failed", "Failed to backup data to the cloud")
    
    def _restore_from_cloud(self):
        """Restore data from cloud"""
        if not self.cloud_integration.is_user_logged_in():
            messagebox.showwarning("Not Logged In", "Please log in to restore from cloud")
            return
        
        if messagebox.askyesno("Restore from Cloud", 
                              "This will replace your local data with cloud data. Continue?"):
            success = self.cloud_integration._sync_data_from_cloud()
            if success:
                messagebox.showinfo("Restore Complete", "Data has been restored from the cloud")
                # Refresh the display
                self.update_display()
            else:
                messagebox.showerror("Restore Failed", "Failed to restore data from the cloud")
    
    def start_recording(self):
        """Override start_recording to sync data before starting"""
        # Sync data to cloud before starting new session
        if self.cloud_integration.is_user_logged_in():
            self.cloud_integration.sync_data_to_cloud()
        
        # Call parent method
        super().start_recording()
    
    def stop_recording(self):
        """Override stop_recording to sync data after stopping"""
        # Call parent method first
        super().stop_recording()
        
        # Sync data to cloud after stopping session
        if self.cloud_integration.is_user_logged_in():
            self.cloud_integration.sync_data_to_cloud()
    
    def on_close(self):
        """Override on_close to sync data before closing"""
        # Sync data to cloud before closing
        if self.cloud_integration.is_user_logged_in():
            self.cloud_integration.sync_data_to_cloud()
        
        # Call parent method
        super().on_close()

def main():
    """Main entry point for the enhanced application"""
    try:
        # Update API base URL for local testing
        cloud_sync_manager.api_base = "http://localhost:5000"
        
        root = tk.Tk()
        app = WordCountAppWithCloud(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        messagebox.showerror("Critical Error", f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()
