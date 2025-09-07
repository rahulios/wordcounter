"""
UI/UX Improvements for Word Counter Pro
Professional styling, themes, and user experience enhancements
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
import json
from pathlib import Path

class ThemeManager:
    """Manages application themes and styling"""
    
    def __init__(self):
        self.themes = {
            "light": {
                "bg": "#ffffff",
                "fg": "#333333",
                "accent": "#0078d4",
                "success": "#107c10",
                "warning": "#ff8c00",
                "error": "#d13438",
                "card_bg": "#f8f9fa",
                "border": "#e1e5e9"
            },
            "dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#0078d4",
                "success": "#107c10",
                "warning": "#ff8c00",
                "error": "#d13438",
                "card_bg": "#2d2d30",
                "border": "#3e3e42"
            },
            "blue": {
                "bg": "#f0f8ff",
                "fg": "#1e3a8a",
                "accent": "#3b82f6",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "card_bg": "#ffffff",
                "border": "#bfdbfe"
            }
        }
        self.current_theme = "light"
    
    def apply_theme(self, root: tk.Tk, theme_name: str):
        """Apply a theme to the application"""
        if theme_name not in self.themes:
            return False
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Configure root window
        root.configure(bg=theme["bg"])
        
        # Configure ttk styles
        style = ttk.Style()
        
        # Configure main styles
        style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        style.configure("TButton", background=theme["accent"], foreground="white")
        style.configure("TEntry", fieldbackground=theme["card_bg"], foreground=theme["fg"])
        style.configure("TFrame", background=theme["bg"])
        
        # Configure custom styles
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 18, "bold"),
                       background=theme["bg"],
                       foreground=theme["fg"])
        
        style.configure("Card.TFrame",
                       background=theme["card_bg"],
                       relief="solid",
                       borderwidth=1)
        
        style.configure("Success.TLabel",
                       foreground=theme["success"],
                       font=("Segoe UI", 10, "bold"))
        
        style.configure("Warning.TLabel",
                       foreground=theme["warning"],
                       font=("Segoe UI", 10, "bold"))
        
        style.configure("Error.TLabel",
                       foreground=theme["error"],
                       font=("Segoe UI", 10, "bold"))
        
        return True

class OnboardingWizard:
    """First-time user onboarding wizard"""
    
    def __init__(self, parent):
        self.parent = parent
        self.wizard_window = None
        self.current_step = 0
        self.user_preferences = {}
    
    def show_wizard(self):
        """Show the onboarding wizard"""
        self.wizard_window = tk.Toplevel(self.parent)
        self.wizard_window.title("Welcome to Word Counter Pro")
        self.wizard_window.geometry("600x500")
        self.wizard_window.resizable(False, False)
        self.wizard_window.transient(self.parent)
        self.wizard_window.grab_set()
        
        # Center the window
        self.wizard_window.update_idletasks()
        x = (self.wizard_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.wizard_window.winfo_screenheight() // 2) - (500 // 2)
        self.wizard_window.geometry(f"600x500+{x}+{y}")
        
        self._create_wizard_ui()
        self._show_step(0)
    
    def _create_wizard_ui(self):
        """Create the wizard UI"""
        main_frame = ttk.Frame(self.wizard_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        self.title_label = ttk.Label(main_frame, text="", style="Title.TLabel")
        self.title_label.pack(pady=(0, 20))
        
        # Content frame
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.back_button = ttk.Button(buttons_frame, text="Back", 
                                     command=self._previous_step, state=tk.DISABLED)
        self.back_button.pack(side=tk.LEFT)
        
        self.next_button = ttk.Button(buttons_frame, text="Next", 
                                     command=self._next_step)
        self.next_button.pack(side=tk.RIGHT)
    
    def _show_step(self, step):
        """Show a specific wizard step"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_step = step
        self.progress_var.set((step / 4) * 100)
        
        if step == 0:
            self._show_welcome_step()
        elif step == 1:
            self._show_goals_step()
        elif step == 2:
            self._show_preferences_step()
        elif step == 3:
            self._show_cloud_setup_step()
        elif step == 4:
            self._show_completion_step()
        
        # Update button states
        self.back_button.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        if step == 4:
            self.next_button.config(text="Finish", command=self._finish_wizard)
        else:
            self.next_button.config(text="Next", command=self._next_step)
    
    def _show_welcome_step(self):
        """Show welcome step"""
        self.title_label.config(text="Welcome to Word Counter Pro!")
        
        welcome_text = """
🎉 Congratulations on choosing Word Counter Pro!

This powerful writing productivity tool will help you:
• Track your writing progress and speed
• Set and achieve writing goals
• Analyze your writing patterns
• Sync your data across devices
• Stay motivated with achievements

Let's get you set up in just a few steps!
        """
        
        ttk.Label(self.content_frame, text=welcome_text, 
                 font=("Segoe UI", 11), justify=tk.LEFT).pack(pady=20)
    
    def _show_goals_step(self):
        """Show goals setup step"""
        self.title_label.config(text="Set Your Writing Goals")
        
        ttk.Label(self.content_frame, text="What are your writing goals?", 
                 font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))
        
        # Daily goal
        goal_frame = ttk.Frame(self.content_frame)
        goal_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(goal_frame, text="Daily word goal:").pack(side=tk.LEFT)
        self.daily_goal_var = tk.StringVar(value="1000")
        ttk.Entry(goal_frame, textvariable=self.daily_goal_var, width=10).pack(side=tk.RIGHT)
        
        # Writing type
        type_frame = ttk.Frame(self.content_frame)
        type_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(type_frame, text="What do you write?").pack(anchor=tk.W)
        self.writing_type_var = tk.StringVar(value="novel")
        
        types = [("Novel/Book", "novel"), ("Blog Posts", "blog"), 
                ("Academic Papers", "academic"), ("Content Marketing", "content"),
                ("Journal/Diary", "journal"), ("Other", "other")]
        
        for text, value in types:
            ttk.Radiobutton(type_frame, text=text, variable=self.writing_type_var, 
                           value=value).pack(anchor=tk.W)
    
    def _show_preferences_step(self):
        """Show preferences step"""
        self.title_label.config(text="Customize Your Experience")
        
        ttk.Label(self.content_frame, text="Choose your preferences:", 
                 font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))
        
        # Theme selection
        theme_frame = ttk.Frame(self.content_frame)
        theme_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").pack(anchor=tk.W)
        self.theme_var = tk.StringVar(value="light")
        
        themes = [("Light", "light"), ("Dark", "dark"), ("Blue", "blue")]
        for text, value in themes:
            ttk.Radiobutton(theme_frame, text=text, variable=self.theme_var, 
                           value=value).pack(anchor=tk.W)
        
        # Notifications
        notif_frame = ttk.Frame(self.content_frame)
        notif_frame.pack(fill=tk.X, pady=10)
        
        self.notifications_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(notif_frame, text="Enable goal achievement notifications", 
                       variable=self.notifications_var).pack(anchor=tk.W)
        
        # Auto-save
        self.auto_save_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(notif_frame, text="Enable auto-save", 
                       variable=self.auto_save_var).pack(anchor=tk.W)
    
    def _show_cloud_setup_step(self):
        """Show cloud setup step"""
        self.title_label.config(text="Cloud Sync Setup")
        
        ttk.Label(self.content_frame, text="Sync your data across devices:", 
                 font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))
        
        cloud_text = """
With cloud sync, you can:
• Access your data from any device
• Never lose your writing progress
• Backup your data securely
• Sync goals and achievements

You can set this up now or later in the app.
        """
        
        ttk.Label(self.content_frame, text=cloud_text, 
                 font=("Segoe UI", 11), justify=tk.LEFT).pack(pady=10)
        
        self.cloud_setup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.content_frame, text="Set up cloud sync now", 
                       variable=self.cloud_setup_var).pack(pady=10)
    
    def _show_completion_step(self):
        """Show completion step"""
        self.title_label.config(text="Setup Complete!")
        
        completion_text = """
🎉 You're all set up and ready to start writing!

Your preferences have been saved and you can change them anytime in Settings.

Click Finish to start using Word Counter Pro!
        """
        
        ttk.Label(self.content_frame, text=completion_text, 
                 font=("Segoe UI", 11), justify=tk.LEFT).pack(pady=20)
    
    def _next_step(self):
        """Go to next step"""
        if self.current_step < 4:
            self._show_step(self.current_step + 1)
    
    def _previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _finish_wizard(self):
        """Finish the wizard"""
        # Save user preferences
        self.user_preferences = {
            "daily_goal": int(self.daily_goal_var.get()),
            "writing_type": self.writing_type_var.get(),
            "theme": self.theme_var.get(),
            "notifications": self.notifications_var.get(),
            "auto_save": self.auto_save_var.get(),
            "cloud_setup": self.cloud_setup_var.get()
        }
        
        # Save to config file
        config_file = Path("user_preferences.json")
        with open(config_file, 'w') as f:
            json.dump(self.user_preferences, f, indent=2)
        
        self.wizard_window.destroy()
        return self.user_preferences

class NotificationManager:
    """Manages system notifications"""
    
    def __init__(self):
        self.notifications_enabled = True
        self.last_notification_time = 0
        self.cooldown = 5  # seconds
    
    def show_goal_achievement(self, goal_type: str, current: int, target: int):
        """Show goal achievement notification"""
        if not self.notifications_enabled:
            return
        
        import time
        current_time = time.time()
        if current_time - self.last_notification_time < self.cooldown:
            return
        
        self.last_notification_time = current_time
        
        message = f"🎉 Goal Achieved!\n\n{goal_type}: {current:,} / {target:,} words"
        messagebox.showinfo("Goal Achieved!", message)
    
    def show_streak_achievement(self, streak_days: int):
        """Show streak achievement notification"""
        if not self.notifications_enabled:
            return
        
        message = f"🔥 Streak Achievement!\n\n{streak_days} days in a row!"
        messagebox.showinfo("Streak Achievement!", message)
    
    def show_welcome_back(self, days_since_last_use: int):
        """Show welcome back notification"""
        if days_since_last_use > 0:
            message = f"Welcome back! It's been {days_since_last_use} days since your last writing session."
            messagebox.showinfo("Welcome Back!", message)

class ProfessionalUI:
    """Professional UI enhancements"""
    
    def __init__(self, root):
        self.root = root
        self.theme_manager = ThemeManager()
        self.notification_manager = NotificationManager()
        self.setup_professional_ui()
    
    def setup_professional_ui(self):
        """Setup professional UI elements"""
        # Configure window
        self.root.configure(bg="#ffffff")
        
        # Set window icon (if available)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Configure ttk styles
        self._configure_styles()
        
        # Add professional touches
        self._add_professional_touches()
    
    def _configure_styles(self):
        """Configure ttk styles for professional look"""
        style = ttk.Style()
        
        # Configure main styles
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TFrame", background="#ffffff")
        
        # Configure custom styles
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 18, "bold"),
                       background="#ffffff",
                       foreground="#333333")
        
        style.configure("Subtitle.TLabel",
                       font=("Segoe UI", 12, "bold"),
                       background="#ffffff",
                       foreground="#666666")
        
        style.configure("Card.TFrame",
                       background="#f8f9fa",
                       relief="solid",
                       borderwidth=1)
        
        style.configure("Success.TLabel",
                       foreground="#107c10",
                       font=("Segoe UI", 10, "bold"))
        
        style.configure("Warning.TLabel",
                       foreground="#ff8c00",
                       font=("Segoe UI", 10, "bold"))
        
        style.configure("Error.TLabel",
                       foreground="#d13438",
                       font=("Segoe UI", 10, "bold"))
    
    def _add_professional_touches(self):
        """Add professional touches to the UI"""
        # Add subtle animations (basic)
        self.root.after(100, self._add_loading_animation)
    
    def _add_loading_animation(self):
        """Add loading animation"""
        # This would be implemented with actual animations
        pass
    
    def create_welcome_screen(self):
        """Create a welcome screen for new users"""
        welcome_frame = ttk.Frame(self.root)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome content
        ttk.Label(welcome_frame, text="Welcome to Word Counter Pro", 
                 style="Title.TLabel").pack(pady=50)
        
        ttk.Label(welcome_frame, text="Your writing productivity companion", 
                 style="Subtitle.TLabel").pack(pady=10)
        
        # Feature highlights
        features = [
            "📊 Real-time writing analytics",
            "🎯 Goal tracking and achievements", 
            "☁️ Cloud sync across devices",
            "🔒 Secure data encryption",
            "📈 Progress visualization"
        ]
        
        for feature in features:
            ttk.Label(welcome_frame, text=feature, 
                     font=("Segoe UI", 11)).pack(pady=5)
        
        # Get started button
        ttk.Button(welcome_frame, text="Get Started", 
                  command=self._start_app).pack(pady=30)
    
    def _start_app(self):
        """Start the main application"""
        # This would transition to the main app
        pass


