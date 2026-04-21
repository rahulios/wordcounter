"""
Mobile Companion App for Word Counter Pro
A lightweight mobile-friendly interface for goal tracking and progress monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
import time

class MobileCompanionApp:
    """Mobile companion app for Word Counter Pro"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Word Counter Pro - Mobile")
        self.root.geometry("400x700")
        self.root.resizable(False, False)
        
        # Configure for mobile-like appearance
        self.root.configure(bg="#f0f0f0")
        
        # API configuration
        self.api_base = "https://your-app-name.herokuapp.com"  # Replace with your Heroku URL
        self.user_token = None
        self.user_profile = None
        
        # Data cache
        self.cached_data = {}
        self.last_sync = None
        
        self.setup_ui()
        self.load_cached_data()
        
        # Start background sync
        self.start_background_sync()
    
    def setup_ui(self):
        """Setup the mobile-like UI"""
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure("Mobile.TLabel", font=("Segoe UI", 12))
        style.configure("Mobile.TButton", font=("Segoe UI", 12), padding=10)
        style.configure("Mobile.TEntry", font=("Segoe UI", 12), padding=8)
        style.configure("Card.TFrame", background="white", relief="solid", borderwidth=1)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # Content area with scrollbar
        self.create_content_area(main_frame)
        
        # Bottom navigation
        self.create_bottom_navigation(main_frame)
    
    def create_header(self, parent):
        """Create the header section"""
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # App title
        title_label = ttk.Label(header_frame, text="Word Counter Pro", 
                               font=("Segoe UI", 18, "bold"))
        title_label.pack(pady=10)
        
        # Sync status
        self.sync_status_label = ttk.Label(header_frame, text="Not connected", 
                                          font=("Segoe UI", 10), foreground="gray")
        self.sync_status_label.pack(pady=(0, 10))
    
    def create_content_area(self, parent):
        """Create the scrollable content area"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content sections
        self.create_dashboard_section(scrollable_frame)
        self.create_goals_section(scrollable_frame)
        self.create_progress_section(scrollable_frame)
        self.create_achievements_section(scrollable_frame)
    
    def create_dashboard_section(self, parent):
        """Create the dashboard section"""
        dashboard_frame = ttk.LabelFrame(parent, text="Today's Progress", 
                                        style="Card.TFrame", padding="15")
        dashboard_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Today's stats
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(fill=tk.X)
        
        # Words written today
        words_frame = ttk.Frame(stats_frame)
        words_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(words_frame, text="Words Today", font=("Segoe UI", 10), 
                 foreground="gray").pack()
        self.words_today_label = ttk.Label(words_frame, text="0", 
                                          font=("Segoe UI", 24, "bold"))
        self.words_today_label.pack()
        
        # Goal progress
        goal_frame = ttk.Frame(stats_frame)
        goal_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(goal_frame, text="Goal Progress", font=("Segoe UI", 10), 
                 foreground="gray").pack()
        self.goal_progress_label = ttk.Label(goal_frame, text="0%", 
                                            font=("Segoe UI", 24, "bold"))
        self.goal_progress_label.pack()
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(dashboard_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.pack(pady=10)
    
    def create_goals_section(self, parent):
        """Create the goals section"""
        goals_frame = ttk.LabelFrame(parent, text="Goals", 
                                    style="Card.TFrame", padding="15")
        goals_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Daily goal
        daily_goal_frame = ttk.Frame(goals_frame)
        daily_goal_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(daily_goal_frame, text="Daily Goal:", style="Mobile.TLabel").pack(side=tk.LEFT)
        self.daily_goal_var = tk.StringVar(value="1000")
        daily_goal_entry = ttk.Entry(daily_goal_frame, textvariable=self.daily_goal_var, 
                                    width=10, style="Mobile.TEntry")
        daily_goal_entry.pack(side=tk.RIGHT)
        
        # Weekly goal
        weekly_goal_frame = ttk.Frame(goals_frame)
        weekly_goal_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(weekly_goal_frame, text="Weekly Goal:", style="Mobile.TLabel").pack(side=tk.LEFT)
        self.weekly_goal_var = tk.StringVar(value="7000")
        weekly_goal_entry = ttk.Entry(weekly_goal_frame, textvariable=self.weekly_goal_var, 
                                     width=10, style="Mobile.TEntry")
        weekly_goal_entry.pack(side=tk.RIGHT)
        
        # Update goals button
        ttk.Button(goals_frame, text="Update Goals", 
                  command=self.update_goals, style="Mobile.TButton").pack(pady=10)
    
    def create_progress_section(self, parent):
        """Create the progress section"""
        progress_frame = ttk.LabelFrame(parent, text="This Week", 
                                       style="Card.TFrame", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Weekly stats
        self.weekly_stats_text = tk.Text(progress_frame, height=6, width=40, 
                                        font=("Segoe UI", 10), wrap=tk.WORD)
        self.weekly_stats_text.pack(fill=tk.X)
        
        # Refresh button
        ttk.Button(progress_frame, text="Refresh", 
                  command=self.refresh_data, style="Mobile.TButton").pack(pady=10)
    
    def create_achievements_section(self, parent):
        """Create the achievements section"""
        achievements_frame = ttk.LabelFrame(parent, text="Recent Achievements", 
                                           style="Card.TFrame", padding="15")
        achievements_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Achievements list
        self.achievements_text = tk.Text(achievements_frame, height=4, width=40, 
                                        font=("Segoe UI", 10), wrap=tk.WORD)
        self.achievements_text.pack(fill=tk.X)
    
    def create_bottom_navigation(self, parent):
        """Create bottom navigation"""
        nav_frame = ttk.Frame(parent, style="Card.TFrame")
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Navigation buttons
        ttk.Button(nav_frame, text="📊 Dashboard", 
                  command=self.show_dashboard, style="Mobile.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="🎯 Goals", 
                  command=self.show_goals, style="Mobile.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="🏆 Achievements", 
                  command=self.show_achievements, style="Mobile.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="⚙️ Settings", 
                  command=self.show_settings, style="Mobile.TButton").pack(side=tk.LEFT, padx=5)
    
    def load_cached_data(self):
        """Load cached data from local storage"""
        try:
            with open("mobile_cache.json", "r") as f:
                self.cached_data = json.load(f)
                self.last_sync = self.cached_data.get("last_sync")
                self.update_ui_with_cached_data()
        except FileNotFoundError:
            self.cached_data = {}
    
    def save_cached_data(self):
        """Save data to local cache"""
        try:
            self.cached_data["last_sync"] = datetime.now().isoformat()
            with open("mobile_cache.json", "w") as f:
                json.dump(self.cached_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def update_ui_with_cached_data(self):
        """Update UI with cached data"""
        if not self.cached_data:
            return
        
        # Update today's progress
        today_data = self.cached_data.get("today", {})
        words_today = today_data.get("words", 0)
        goal = today_data.get("goal", 1000)
        
        self.words_today_label.config(text=str(words_today))
        progress = (words_today / goal) * 100 if goal > 0 else 0
        self.goal_progress_label.config(text=f"{progress:.0f}%")
        self.progress_var.set(progress)
        
        # Update weekly stats
        weekly_data = self.cached_data.get("weekly", {})
        self.update_weekly_stats_display(weekly_data)
        
        # Update achievements
        achievements = self.cached_data.get("achievements", [])
        self.update_achievements_display(achievements)
    
    def update_weekly_stats_display(self, weekly_data):
        """Update weekly stats display"""
        self.weekly_stats_text.delete(1.0, tk.END)
        
        if not weekly_data:
            self.weekly_stats_text.insert(tk.END, "No data available")
            return
        
        total_words = weekly_data.get("total_words", 0)
        avg_daily = weekly_data.get("avg_daily", 0)
        best_day = weekly_data.get("best_day", "N/A")
        
        stats_text = f"""Total Words: {total_words:,}
Average Daily: {avg_daily:.0f}
Best Day: {best_day}
Streak: {weekly_data.get("streak", 0)} days"""
        
        self.weekly_stats_text.insert(tk.END, stats_text)
    
    def update_achievements_display(self, achievements):
        """Update achievements display"""
        self.achievements_text.delete(1.0, tk.END)
        
        if not achievements:
            self.achievements_text.insert(tk.END, "No achievements yet")
            return
        
        # Show recent achievements
        recent_achievements = achievements[-3:]  # Last 3 achievements
        
        for achievement in recent_achievements:
            name = achievement.get("name", "Unknown")
            date = achievement.get("date", "Unknown")
            self.achievements_text.insert(tk.END, f"🏆 {name} ({date})\n")
    
    def start_background_sync(self):
        """Start background synchronization"""
        def sync_loop():
            while True:
                try:
                    self.sync_with_server()
                    time.sleep(300)  # Sync every 5 minutes
                except Exception as e:
                    print(f"Sync error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        sync_thread = threading.Thread(target=sync_loop, daemon=True)
        sync_thread.start()
    
    def sync_with_server(self):
        """Sync data with the server"""
        try:
            # This would sync with your actual API
            # For now, we'll just update the sync status
            self.sync_status_label.config(text="Synced", foreground="green")
            self.last_sync = datetime.now()
        except Exception as e:
            self.sync_status_label.config(text="Sync failed", foreground="red")
            print(f"Sync error: {e}")
    
    def update_goals(self):
        """Update user goals"""
        try:
            daily_goal = int(self.daily_goal_var.get())
            weekly_goal = int(self.weekly_goal_var.get())
            
            # Update local cache
            self.cached_data["goals"] = {
                "daily": daily_goal,
                "weekly": weekly_goal
            }
            self.save_cached_data()
            
            messagebox.showinfo("Success", "Goals updated successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for goals")
    
    def refresh_data(self):
        """Refresh data from server"""
        self.sync_with_server()
        self.update_ui_with_cached_data()
        messagebox.showinfo("Refreshed", "Data refreshed successfully!")
    
    def show_dashboard(self):
        """Show dashboard view"""
        messagebox.showinfo("Dashboard", "Dashboard view selected")
    
    def show_goals(self):
        """Show goals view"""
        messagebox.showinfo("Goals", "Goals view selected")
    
    def show_achievements(self):
        """Show achievements view"""
        messagebox.showinfo("Achievements", "Achievements view selected")
    
    def show_settings(self):
        """Show settings view"""
        messagebox.showinfo("Settings", "Settings view selected")
    
    def run(self):
        """Run the mobile companion app"""
        self.root.mainloop()

def main():
    """Main entry point for mobile companion"""
    app = MobileCompanionApp()
    app.run()

if __name__ == "__main__":
    main()


