"""
Cloud Integration Module for Word Counter Pro
Integrates cloud sync functionality with the existing WordCounter application
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
import time

from cloud_sync import cloud_sync_manager, UserProfile
from auth_ui import LoginDialog, RegisterDialog, AccountManagerDialog, SyncStatusWidget

class CloudIntegration:
    """Integrates cloud sync with the main WordCounter application"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.sync_widget = None
        self.auto_sync_enabled = True
        self.sync_interval = 300  # 5 minutes
        self.last_sync_data = None
        
        # Load user data on startup
        self._load_user_session()
        
    def _load_user_session(self):
        """Load user session on startup"""
        try:
            if cloud_sync_manager.load_user_data():
                logging.info(f"User session loaded: {cloud_sync_manager.user_profile.username}")
                # Check connectivity
                cloud_sync_manager.check_connectivity()
            else:
                logging.info("No user session found")
        except Exception as e:
            logging.error(f"Error loading user session: {e}")
    
    def show_login_dialog(self):
        """Show login dialog"""
        def on_login_success(profile: UserProfile):
            logging.info(f"User logged in: {profile.username}")
            self._update_ui_after_login()
            # Sync data after login
            self._sync_data_from_cloud()
        
        login_dialog = LoginDialog(self.main_app.root, on_login_success)
        login_dialog.show()
    
    def show_register_dialog(self):
        """Show registration dialog"""
        def on_register_success(profile: UserProfile):
            logging.info(f"User registered: {profile.username}")
            self._update_ui_after_login()
            # No need to sync on registration as there's no data yet
        
        register_dialog = RegisterDialog(self.main_app.root, on_register_success)
        register_dialog.show()
    
    def show_account_manager(self):
        """Show account management dialog"""
        account_dialog = AccountManagerDialog(self.main_app.root)
        account_dialog.show()
    
    def create_sync_widget(self, parent_frame):
        """Create sync status widget for the main UI"""
        self.sync_widget = SyncStatusWidget(parent_frame)
        self.sync_widget.create_widget(parent_frame)
        return self.sync_widget
    
    def _update_ui_after_login(self):
        """Update UI after successful login"""
        if self.sync_widget:
            self.sync_widget.update_status()
        
        # Update menu items
        self._update_menu_items()
    
    def _update_menu_items(self):
        """Update menu items based on login status"""
        # This would be called to update the main app's menu
        # For now, we'll just log the status
        if cloud_sync_manager.user_profile:
            logging.info("User is logged in - updating menu items")
        else:
            logging.info("User is not logged in - updating menu items")
    
    def sync_data_to_cloud(self, force: bool = False) -> bool:
        """Sync local data to cloud"""
        if not cloud_sync_manager.user_profile or not cloud_sync_manager.is_online:
            logging.warning("Cannot sync: user not logged in or offline")
            return False
        
        try:
            # Prepare local data for sync
            local_data = self._prepare_local_data()
            
            # Check if data has changed
            if not force and self._data_unchanged(local_data):
                logging.info("No data changes detected, skipping sync")
                return True
            
            # Sync to cloud
            success, message = cloud_sync_manager.sync_data_to_cloud(local_data)
            
            if success:
                logging.info("Data synced to cloud successfully")
                self.last_sync_data = local_data
                if self.sync_widget:
                    self.sync_widget.update_status()
                return True
            else:
                logging.error(f"Failed to sync data to cloud: {message}")
                return False
                
        except Exception as e:
            logging.error(f"Error syncing data to cloud: {e}")
            return False
    
    def _sync_data_from_cloud(self) -> bool:
        """Sync data from cloud to local"""
        if not cloud_sync_manager.user_profile or not cloud_sync_manager.is_online:
            logging.warning("Cannot sync: user not logged in or offline")
            return False
        
        try:
            # Sync from cloud
            success, message, cloud_data = cloud_sync_manager.sync_data_from_cloud()
            
            if success and cloud_data:
                logging.info("Data synced from cloud successfully")
                self._apply_cloud_data(cloud_data)
                if self.sync_widget:
                    self.sync_widget.update_status()
                return True
            elif success and not cloud_data:
                logging.info("No cloud data found")
                return True
            else:
                logging.error(f"Failed to sync data from cloud: {message}")
                return False
                
        except Exception as e:
            logging.error(f"Error syncing data from cloud: {e}")
            return False
    
    def _prepare_local_data(self) -> Dict[str, Any]:
        """Prepare local data for cloud sync"""
        try:
            # Get data from the main app
            local_data = {
                "sessions": [],
                "goals": [],
                "achievements": [],
                "settings": {},
                "version": 1,
                "last_modified": datetime.now().isoformat()
            }
            
            # Get sessions from data manager
            if hasattr(self.main_app, 'data_manager') and self.main_app.data_manager.data_file.exists():
                import pandas as pd
                df = pd.read_excel(self.main_app.data_manager.data_file)
                
                sessions = []
                for _, row in df.iterrows():
                    session = {
                        "date_time": row['Date and Time'].isoformat() if hasattr(row['Date and Time'], 'isoformat') else str(row['Date and Time']),
                        "word_count": int(row['Word Count']),
                        "duration": int(row.get('Duration (seconds)', 0)),
                        "wpm": float(row.get('WPM', 0)),
                        "productivity_score": float(row.get('Productivity Score', 0))
                    }
                    sessions.append(session)
                
                local_data["sessions"] = sessions
            
            # Get goals from goal manager
            if hasattr(self.main_app, 'goal_manager'):
                goals = []
                for goal in self.main_app.goal_manager.get_active_goals():
                    goal_data = {
                        "goal_id": goal.goal_id,
                        "goal_type": goal.goal_type,
                        "target_words": goal.target_words,
                        "start_date": goal.start_date.isoformat(),
                        "end_date": goal.end_date.isoformat() if goal.end_date else None,
                        "current_progress": goal.current_progress,
                        "completed": goal.completed,
                        "created_date": goal.created_date.isoformat()
                    }
                    goals.append(goal_data)
                
                local_data["goals"] = goals
            
            # Get achievements from analytics
            if hasattr(self.main_app, 'analytics'):
                achievements = []
                for achievement in self.main_app.analytics.achievements:
                    achievement_data = {
                        "achievement_id": achievement.achievement_id,
                        "name": achievement.name,
                        "description": achievement.description,
                        "category": achievement.category,
                        "criteria": achievement.criteria,
                        "unlocked_date": achievement.unlocked_date.isoformat() if achievement.unlocked_date else None,
                        "icon": achievement.icon
                    }
                    achievements.append(achievement_data)
                
                local_data["achievements"] = achievements
            
            # Get settings from config
            if hasattr(self.main_app, 'config'):
                local_data["settings"] = self.main_app.config.config.copy()
            
            return local_data
            
        except Exception as e:
            logging.error(f"Error preparing local data: {e}")
            return {"sessions": [], "goals": [], "achievements": [], "settings": {}, "version": 1}
    
    def _apply_cloud_data(self, cloud_data: Dict[str, Any]):
        """Apply cloud data to local application"""
        try:
            # Apply sessions data
            if cloud_data.get("sessions"):
                self._apply_sessions_data(cloud_data["sessions"])
            
            # Apply goals data
            if cloud_data.get("goals"):
                self._apply_goals_data(cloud_data["goals"])
            
            # Apply achievements data
            if cloud_data.get("achievements"):
                self._apply_achievements_data(cloud_data["achievements"])
            
            # Apply settings data
            if cloud_data.get("settings"):
                self._apply_settings_data(cloud_data["settings"])
            
            logging.info("Cloud data applied to local application")
            
        except Exception as e:
            logging.error(f"Error applying cloud data: {e}")
    
    def _apply_sessions_data(self, sessions_data: List[Dict[str, Any]]):
        """Apply sessions data to local storage"""
        try:
            import pandas as pd
            from datetime import datetime
            
            # Convert sessions to DataFrame
            sessions_list = []
            for session in sessions_data:
                session_dict = {
                    'Date and Time': pd.to_datetime(session['date_time']),
                    'Word Count': session['word_count'],
                    'Duration (seconds)': session['duration'],
                    'WPM': session['wpm'],
                    'Productivity Score': session['productivity_score']
                }
                sessions_list.append(session_dict)
            
            if sessions_list:
                df = pd.DataFrame(sessions_list)
                
                # Save to Excel file
                if hasattr(self.main_app, 'data_manager'):
                    df.to_excel(self.main_app.data_manager.data_file, index=False)
                    logging.info(f"Applied {len(sessions_list)} sessions from cloud")
            
        except Exception as e:
            logging.error(f"Error applying sessions data: {e}")
    
    def _apply_goals_data(self, goals_data: List[Dict[str, Any]]):
        """Apply goals data to local storage"""
        try:
            if hasattr(self.main_app, 'goal_manager'):
                # Clear existing goals
                self.main_app.goal_manager.goals.clear()
                
                # Add goals from cloud
                for goal_data in goals_data:
                    from wordcounter_09_06_25 import WritingGoal
                    from datetime import datetime
                    
                    goal = WritingGoal(
                        goal_id=goal_data['goal_id'],
                        goal_type=goal_data['goal_type'],
                        target_words=goal_data['target_words'],
                        start_date=datetime.fromisoformat(goal_data['start_date']),
                        end_date=datetime.fromisoformat(goal_data['end_date']) if goal_data.get('end_date') else None,
                        current_progress=goal_data['current_progress'],
                        completed=goal_data['completed'],
                        created_date=datetime.fromisoformat(goal_data['created_date'])
                    )
                    self.main_app.goal_manager.goals.append(goal)
                
                logging.info(f"Applied {len(goals_data)} goals from cloud")
            
        except Exception as e:
            logging.error(f"Error applying goals data: {e}")
    
    def _apply_achievements_data(self, achievements_data: List[Dict[str, Any]]):
        """Apply achievements data to local storage"""
        try:
            if hasattr(self.main_app, 'analytics'):
                # Clear existing achievements
                self.main_app.analytics.achievements.clear()
                
                # Add achievements from cloud
                for achievement_data in achievements_data:
                    from wordcounter_09_06_25 import Achievement
                    from datetime import datetime
                    
                    achievement = Achievement(
                        achievement_id=achievement_data['achievement_id'],
                        name=achievement_data['name'],
                        description=achievement_data['description'],
                        category=achievement_data['category'],
                        criteria=achievement_data['criteria'],
                        unlocked_date=datetime.fromisoformat(achievement_data['unlocked_date']) if achievement_data.get('unlocked_date') else None,
                        icon=achievement_data.get('icon', '🏆')
                    )
                    self.main_app.analytics.achievements.append(achievement)
                
                logging.info(f"Applied {len(achievements_data)} achievements from cloud")
            
        except Exception as e:
            logging.error(f"Error applying achievements data: {e}")
    
    def _apply_settings_data(self, settings_data: Dict[str, Any]):
        """Apply settings data to local storage"""
        try:
            if hasattr(self.main_app, 'config'):
                # Update config with cloud settings
                for key, value in settings_data.items():
                    if key in self.main_app.config.config:
                        self.main_app.config.config[key] = value
                
                # Save updated config
                self.main_app.config.save_config()
                logging.info("Applied settings from cloud")
            
        except Exception as e:
            logging.error(f"Error applying settings data: {e}")
    
    def _data_unchanged(self, current_data: Dict[str, Any]) -> bool:
        """Check if data has changed since last sync"""
        if not self.last_sync_data:
            return False
        
        # Simple comparison - in production, you'd want more sophisticated change detection
        return (current_data.get("sessions") == self.last_sync_data.get("sessions") and
                current_data.get("goals") == self.last_sync_data.get("goals") and
                current_data.get("achievements") == self.last_sync_data.get("achievements"))
    
    def start_auto_sync(self):
        """Start automatic background syncing"""
        if self.auto_sync_enabled and cloud_sync_manager.user_profile:
            def auto_sync_loop():
                while self.auto_sync_enabled and cloud_sync_manager.user_profile:
                    try:
                        # Sync data to cloud
                        self.sync_data_to_cloud()
                        time.sleep(self.sync_interval)
                    except Exception as e:
                        logging.error(f"Auto sync error: {e}")
                        time.sleep(60)  # Wait 1 minute on error
            
            sync_thread = threading.Thread(target=auto_sync_loop, daemon=True)
            sync_thread.start()
            logging.info("Auto sync started")
    
    def stop_auto_sync(self):
        """Stop automatic background syncing"""
        self.auto_sync_enabled = False
        logging.info("Auto sync stopped")
    
    def manual_sync(self):
        """Perform manual sync"""
        if not cloud_sync_manager.user_profile:
            messagebox.showwarning("Not Logged In", "Please log in to sync data")
            return
        
        if not cloud_sync_manager.is_online:
            messagebox.showwarning("Offline", "Cannot sync while offline. Please check your internet connection.")
            return
        
        # Show progress dialog
        progress_dialog = tk.Toplevel(self.main_app.root)
        progress_dialog.title("Syncing Data")
        progress_dialog.geometry("300x100")
        progress_dialog.transient(self.main_app.root)
        progress_dialog.grab_set()
        
        # Center the dialog
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (100 // 2)
        progress_dialog.geometry(f"300x100+{x}+{y}")
        
        ttk.Label(progress_dialog, text="Syncing data...", font=("Helvetica", 12)).pack(pady=20)
        progress_dialog.update()
        
        # Perform sync
        success = self.sync_data_to_cloud(force=True)
        
        progress_dialog.destroy()
        
        if success:
            messagebox.showinfo("Sync Complete", "Data synced successfully!")
        else:
            messagebox.showerror("Sync Failed", "Failed to sync data. Please try again.")
    
    def is_user_logged_in(self) -> bool:
        """Check if user is logged in"""
        return cloud_sync_manager.user_profile is not None
    
    def get_user_profile(self) -> Optional[UserProfile]:
        """Get current user profile"""
        return cloud_sync_manager.user_profile
    
    def logout_user(self):
        """Logout current user"""
        cloud_sync_manager.logout_user()
        if self.sync_widget:
            self.sync_widget.update_status()
        self._update_menu_items()
        logging.info("User logged out")
