"""
User Authentication UI Components for Word Counter Pro
Provides login, registration, and account management dialogs
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable
import re
from cloud_sync import cloud_sync_manager, UserProfile

class LoginDialog:
    """Login dialog for existing users"""
    
    def __init__(self, parent, on_success: Callable[[UserProfile], None]):
        self.parent = parent
        self.on_success = on_success
        self.dialog = None
        self.result = None
        
    def show(self):
        """Show the login dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Login - Word Counter Pro")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the login UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Login to Word Counter Pro", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Username/Email field
        ttk.Label(main_frame, text="Username or Email:").pack(anchor=tk.W, pady=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        username_entry.pack(fill=tk.X, pady=(0, 15))
        username_entry.focus()
        
        # Password field
        ttk.Label(main_frame, text="Password:").pack(anchor=tk.W, pady=(0, 5))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                  show="*", width=30)
        password_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Remember me checkbox
        self.remember_var = tk.BooleanVar(value=True)
        remember_check = ttk.Checkbutton(main_frame, text="Remember me", 
                                        variable=self.remember_var)
        remember_check.pack(anchor=tk.W, pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Login button
        login_button = ttk.Button(buttons_frame, text="Login", 
                                 command=self._handle_login, width=15)
        login_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                  command=self._handle_cancel, width=15)
        cancel_button.pack(side=tk.LEFT)
        
        # Register link
        register_frame = ttk.Frame(main_frame)
        register_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(register_frame, text="Don't have an account?").pack(side=tk.LEFT)
        register_link = ttk.Button(register_frame, text="Register here", 
                                  command=self._show_register, style="Link.TButton")
        register_link.pack(side=tk.LEFT, padx=(5, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="red")
        self.status_label.pack(pady=(10, 0))
        
        # Bind Enter key to login
        self.dialog.bind('<Return>', lambda e: self._handle_login())
        
    def _handle_login(self):
        """Handle login button click"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            self.status_label.config(text="Please enter both username and password")
            return
        
        # Show loading state
        self.status_label.config(text="Logging in...", foreground="blue")
        self.dialog.update()
        
        # Attempt login
        success, message = cloud_sync_manager.login_user(username, password)
        
        if success:
            self.status_label.config(text="Login successful!", foreground="green")
            self.dialog.after(1000, self._login_success)
        else:
            self.status_label.config(text=message, foreground="red")
    
    def _login_success(self):
        """Handle successful login"""
        if self.on_success:
            self.on_success(cloud_sync_manager.user_profile)
        self.dialog.destroy()
    
    def _handle_cancel(self):
        """Handle cancel button click"""
        self.dialog.destroy()
    
    def _show_register(self):
        """Show registration dialog"""
        self.dialog.destroy()
        register_dialog = RegisterDialog(self.parent, self.on_success)
        register_dialog.show()

class RegisterDialog:
    """Registration dialog for new users"""
    
    def __init__(self, parent, on_success: Callable[[UserProfile], None]):
        self.parent = parent
        self.on_success = on_success
        self.dialog = None
        
    def show(self):
        """Show the registration dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Register - Word Counter Pro")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"450x400+{x}+{y}")
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the registration UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Create Account - Word Counter Pro", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Email field
        ttk.Label(main_frame, text="Email Address:").pack(anchor=tk.W, pady=(0, 5))
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=35)
        email_entry.pack(fill=tk.X, pady=(0, 15))
        email_entry.focus()
        
        # Username field
        ttk.Label(main_frame, text="Username:").pack(anchor=tk.W, pady=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=35)
        username_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Display name field
        ttk.Label(main_frame, text="Display Name (optional):").pack(anchor=tk.W, pady=(0, 5))
        self.display_name_var = tk.StringVar()
        display_name_entry = ttk.Entry(main_frame, textvariable=self.display_name_var, width=35)
        display_name_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Password field
        ttk.Label(main_frame, text="Password:").pack(anchor=tk.W, pady=(0, 5))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, 
                                  show="*", width=35)
        password_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Password requirements
        requirements_label = ttk.Label(main_frame, 
                                      text="Password must be at least 8 characters long",
                                      font=("Helvetica", 9), foreground="gray")
        requirements_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Terms and conditions
        terms_frame = ttk.Frame(main_frame)
        terms_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.terms_var = tk.BooleanVar()
        terms_check = ttk.Checkbutton(terms_frame, text="I agree to the Terms of Service and Privacy Policy",
                                     variable=self.terms_var)
        terms_check.pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Register button
        register_button = ttk.Button(buttons_frame, text="Create Account", 
                                    command=self._handle_register, width=18)
        register_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                  command=self._handle_cancel, width=18)
        cancel_button.pack(side=tk.LEFT)
        
        # Login link
        login_frame = ttk.Frame(main_frame)
        login_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(login_frame, text="Already have an account?").pack(side=tk.LEFT)
        login_link = ttk.Button(login_frame, text="Login here", 
                               command=self._show_login, style="Link.TButton")
        login_link.pack(side=tk.LEFT, padx=(5, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="red")
        self.status_label.pack(pady=(10, 0))
        
        # Bind Enter key to register
        self.dialog.bind('<Return>', lambda e: self._handle_register())
        
    def _handle_register(self):
        """Handle register button click"""
        email = self.email_var.get().strip()
        username = self.username_var.get().strip()
        display_name = self.display_name_var.get().strip()
        password = self.password_var.get()
        
        # Validate input
        if not email or not username or not password:
            self.status_label.config(text="Please fill in all required fields")
            return
        
        if not self.terms_var.get():
            self.status_label.config(text="Please agree to the Terms of Service")
            return
        
        if not self._validate_email(email):
            self.status_label.config(text="Please enter a valid email address")
            return
        
        if len(password) < 8:
            self.status_label.config(text="Password must be at least 8 characters long")
            return
        
        if not self._validate_username(username):
            self.status_label.config(text="Username can only contain letters, numbers, and underscores")
            return
        
        # Show loading state
        self.status_label.config(text="Creating account...", foreground="blue")
        self.dialog.update()
        
        # Attempt registration
        success, message = cloud_sync_manager.register_user(email, username, password, display_name)
        
        if success:
            self.status_label.config(text="Account created successfully!", foreground="green")
            self.dialog.after(1000, self._register_success)
        else:
            self.status_label.config(text=message, foreground="red")
    
    def _register_success(self):
        """Handle successful registration"""
        if self.on_success:
            self.on_success(cloud_sync_manager.user_profile)
        self.dialog.destroy()
    
    def _handle_cancel(self):
        """Handle cancel button click"""
        self.dialog.destroy()
    
    def _show_login(self):
        """Show login dialog"""
        self.dialog.destroy()
        login_dialog = LoginDialog(self.parent, self.on_success)
        login_dialog.show()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        pattern = r'^[a-zA-Z0-9_]+$'
        return re.match(pattern, username) is not None and len(username) >= 3

class AccountManagerDialog:
    """Account management dialog for logged-in users"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        
    def show(self):
        """Show the account management dialog"""
        if not cloud_sync_manager.user_profile:
            messagebox.showwarning("Not Logged In", "Please log in to manage your account")
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Account Management - Word Counter Pro")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the account management UI"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Account Management", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # User info frame
        info_frame = ttk.LabelFrame(main_frame, text="Account Information", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        profile = cloud_sync_manager.user_profile
        
        # Username
        ttk.Label(info_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=profile.username, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Email
        ttk.Label(info_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=profile.email, font=("Helvetica", 10, "bold")).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Display name
        ttk.Label(info_frame, text="Display Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=profile.display_name, font=("Helvetica", 10, "bold")).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Subscription tier
        ttk.Label(info_frame, text="Subscription:").grid(row=3, column=0, sticky=tk.W, pady=2)
        tier_label = ttk.Label(info_frame, text=profile.subscription_tier.title(), 
                              font=("Helvetica", 10, "bold"), foreground="blue")
        tier_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Member since
        ttk.Label(info_frame, text="Member Since:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=profile.created_at.strftime("%B %d, %Y"), 
                 font=("Helvetica", 10, "bold")).grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Sync status frame
        sync_frame = ttk.LabelFrame(main_frame, text="Sync Status", padding="15")
        sync_frame.pack(fill=tk.X, pady=(0, 20))
        
        sync_status = cloud_sync_manager.get_sync_status()
        
        # Online status
        status_text = "Online" if sync_status["is_online"] else "Offline"
        status_color = "green" if sync_status["is_online"] else "red"
        ttk.Label(sync_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(sync_frame, text=status_text, font=("Helvetica", 10, "bold"), 
                 foreground=status_color).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Last sync
        last_sync_text = "Never" if not sync_status["last_sync"] else sync_status["last_sync"]
        ttk.Label(sync_frame, text="Last Sync:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(sync_frame, text=last_sync_text, font=("Helvetica", 10, "bold")).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Sync now button
        sync_button = ttk.Button(buttons_frame, text="Sync Now", 
                                command=self._sync_now, width=15)
        sync_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Upgrade button (if free tier)
        if profile.subscription_tier == "free":
            upgrade_button = ttk.Button(buttons_frame, text="Upgrade to Pro", 
                                       command=self._upgrade_account, width=15)
            upgrade_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Logout button
        logout_button = ttk.Button(buttons_frame, text="Logout", 
                                  command=self._logout, width=15)
        logout_button.pack(side=tk.RIGHT)
        
    def _sync_now(self):
        """Handle sync now button click"""
        # This would trigger a manual sync
        messagebox.showinfo("Sync", "Sync functionality will be implemented with the main app integration")
    
    def _upgrade_account(self):
        """Handle upgrade button click"""
        messagebox.showinfo("Upgrade", "Upgrade functionality will be implemented with payment integration")
    
    def _logout(self):
        """Handle logout button click"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            cloud_sync_manager.logout_user()
            self.dialog.destroy()
            messagebox.showinfo("Logged Out", "You have been logged out successfully")

class SyncStatusWidget:
    """Widget to show sync status in the main window"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = None
        self.status_label = None
        self.sync_button = None
        
    def create_widget(self, parent_frame):
        """Create the sync status widget"""
        self.frame = ttk.Frame(parent_frame)
        self.frame.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.frame, text="Not logged in", 
                                     font=("Helvetica", 9))
        self.status_label.pack(side=tk.LEFT)
        
        # Sync button
        self.sync_button = ttk.Button(self.frame, text="Sync", 
                                     command=self._manual_sync, state=tk.DISABLED)
        self.sync_button.pack(side=tk.RIGHT)
        
        # Update status
        self.update_status()
        
    def update_status(self):
        """Update the sync status display"""
        if cloud_sync_manager.user_profile:
            sync_status = cloud_sync_manager.get_sync_status()
            if sync_status["is_online"]:
                status_text = f"✓ {cloud_sync_manager.user_profile.username} - Online"
                self.status_label.config(text=status_text, foreground="green")
                self.sync_button.config(state=tk.NORMAL)
            else:
                status_text = f"✗ {cloud_sync_manager.user_profile.username} - Offline"
                self.status_label.config(text=status_text, foreground="red")
                self.sync_button.config(state=tk.DISABLED)
        else:
            self.status_label.config(text="Not logged in", foreground="gray")
            self.sync_button.config(state=tk.DISABLED)
    
    def _manual_sync(self):
        """Handle manual sync button click"""
        # This would trigger a manual sync
        messagebox.showinfo("Sync", "Manual sync functionality will be implemented with the main app integration")
