"""
Setup script for Word Counter Pro Cloud Sync
This script helps users set up the cloud sync functionality
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from pathlib import Path

class CloudSyncSetup:
    """Setup wizard for cloud sync functionality"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Word Counter Pro - Cloud Sync Setup")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")
        
        self.current_step = 0
        self.setup_complete = False
        
    def run(self):
        """Run the setup wizard"""
        self._create_ui()
        self._show_step(0)
        self.root.mainloop()
    
    def _create_ui(self):
        """Create the setup UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Word Counter Pro - Cloud Sync Setup", 
                               font=("Helvetica", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
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
        
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                       command=self._cancel_setup)
        self.cancel_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def _show_step(self, step):
        """Show a specific setup step"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_step = step
        self.progress_var.set((step / 4) * 100)
        
        if step == 0:
            self._show_welcome_step()
        elif step == 1:
            self._show_dependencies_step()
        elif step == 2:
            self._show_backend_step()
        elif step == 3:
            self._show_configuration_step()
        elif step == 4:
            self._show_completion_step()
        
        # Update button states
        self.back_button.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        if step == 4:
            self.next_button.config(text="Finish", command=self._finish_setup)
        else:
            self.next_button.config(text="Next", command=self._next_step)
    
    def _show_welcome_step(self):
        """Show welcome step"""
        welcome_frame = ttk.Frame(self.content_frame)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome text
        welcome_text = """
Welcome to Word Counter Pro Cloud Sync Setup!

This wizard will help you set up cloud synchronization for your Word Counter Pro application.

With cloud sync, you can:
• Sync your writing data across multiple devices
• Backup your data securely in the cloud
• Access your writing statistics from anywhere
• Collaborate with other writers

The setup process includes:
1. Installing required dependencies
2. Setting up a local backend server for testing
3. Configuring cloud sync settings
4. Testing the connection

Click Next to begin the setup process.
        """
        
        ttk.Label(welcome_frame, text=welcome_text, justify=tk.LEFT, 
                 font=("Helvetica", 11)).pack(pady=20)
    
    def _show_dependencies_step(self):
        """Show dependencies installation step"""
        deps_frame = ttk.Frame(self.content_frame)
        deps_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(deps_frame, text="Installing Dependencies", 
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Dependencies list
        deps_text = """
The following Python packages are required for cloud sync:

• requests - For HTTP communication with the cloud server
• cryptography - For encrypting data before cloud storage

These packages will be installed automatically.
        """
        
        ttk.Label(deps_frame, text=deps_text, justify=tk.LEFT, 
                 font=("Helvetica", 11)).pack(pady=(0, 20))
        
        # Install button
        install_button = ttk.Button(deps_frame, text="Install Dependencies", 
                                   command=self._install_dependencies)
        install_button.pack(pady=10)
        
        # Status label
        self.deps_status_label = ttk.Label(deps_frame, text="", foreground="blue")
        self.deps_status_label.pack(pady=10)
    
    def _show_backend_step(self):
        """Show backend server setup step"""
        backend_frame = ttk.Frame(self.content_frame)
        backend_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(backend_frame, text="Backend Server Setup", 
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Backend explanation
        backend_text = """
For testing purposes, you can run a local backend server.

The backend server provides:
• User authentication (login/register)
• Data synchronization endpoints
• Secure data storage

To start the backend server:
1. Open a new terminal/command prompt
2. Navigate to your WordCounter folder
3. Run: python backend_server.py

The server will be available at: http://localhost:5000
        """
        
        ttk.Label(backend_frame, text=backend_text, justify=tk.LEFT, 
                 font=("Helvetica", 11)).pack(pady=(0, 20))
        
        # Start server button
        start_server_button = ttk.Button(backend_frame, text="Start Backend Server", 
                                        command=self._start_backend_server)
        start_server_button.pack(pady=10)
        
        # Status label
        self.backend_status_label = ttk.Label(backend_frame, text="", foreground="blue")
        self.backend_status_label.pack(pady=10)
    
    def _show_configuration_step(self):
        """Show configuration step"""
        config_frame = ttk.Frame(self.content_frame)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(config_frame, text="Configuration", 
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Configuration options
        config_text = """
Configure your cloud sync settings:

• Auto-sync: Automatically sync data every 5 minutes
• Data encryption: Your data is encrypted before cloud storage
• Offline mode: Continue working when offline, sync when connected

You can change these settings later in the application.
        """
        
        ttk.Label(config_frame, text=config_text, justify=tk.LEFT, 
                 font=("Helvetica", 11)).pack(pady=(0, 20))
        
        # Configuration checkboxes
        self.auto_sync_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable auto-sync", 
                       variable=self.auto_sync_var).pack(anchor=tk.W, pady=5)
        
        self.encryption_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable data encryption", 
                       variable=self.encryption_var, state=tk.DISABLED).pack(anchor=tk.W, pady=5)
        
        self.offline_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable offline mode", 
                       variable=self.offline_mode_var).pack(anchor=tk.W, pady=5)
    
    def _show_completion_step(self):
        """Show completion step"""
        completion_frame = ttk.Frame(self.content_frame)
        completion_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(completion_frame, text="Setup Complete!", 
                 font=("Helvetica", 16, "bold"), foreground="green").pack(pady=(0, 20))
        
        # Completion text
        completion_text = """
Cloud sync has been successfully configured!

Next steps:
1. Start the backend server (if not already running)
2. Launch Word Counter Pro with cloud sync
3. Create an account or login
4. Start writing and syncing!

To launch the enhanced app, run:
python wordcounter_with_cloud.py

For support, visit: https://github.com/your-repo/wordcounter-pro
        """
        
        ttk.Label(completion_frame, text=completion_text, justify=tk.LEFT, 
                 font=("Helvetica", 11)).pack(pady=20)
        
        # Launch button
        launch_button = ttk.Button(completion_frame, text="Launch Word Counter Pro", 
                                  command=self._launch_app)
        launch_button.pack(pady=10)
    
    def _install_dependencies(self):
        """Install required dependencies"""
        self.deps_status_label.config(text="Installing dependencies...", foreground="blue")
        self.root.update()
        
        try:
            # Install dependencies
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            self.deps_status_label.config(text="Dependencies installed successfully!", foreground="green")
        except subprocess.CalledProcessError as e:
            self.deps_status_label.config(text=f"Failed to install dependencies: {e}", foreground="red")
        except Exception as e:
            self.deps_status_label.config(text=f"Error: {e}", foreground="red")
    
    def _start_backend_server(self):
        """Start the backend server"""
        self.backend_status_label.config(text="Starting backend server...", foreground="blue")
        self.root.update()
        
        try:
            # Start server in a new process
            subprocess.Popen([sys.executable, "backend_server.py"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            self.backend_status_label.config(text="Backend server started! Check the new console window.", foreground="green")
        except Exception as e:
            self.backend_status_label.config(text=f"Failed to start server: {e}", foreground="red")
    
    def _launch_app(self):
        """Launch the enhanced Word Counter Pro app"""
        try:
            subprocess.Popen([sys.executable, "wordcounter_with_cloud.py"])
            self.setup_complete = True
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch app: {e}")
    
    def _next_step(self):
        """Go to next step"""
        if self.current_step < 4:
            self._show_step(self.current_step + 1)
    
    def _previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _cancel_setup(self):
        """Cancel setup"""
        if messagebox.askyesno("Cancel Setup", "Are you sure you want to cancel the setup?"):
            self.root.destroy()
    
    def _finish_setup(self):
        """Finish setup"""
        self.setup_complete = True
        self.root.destroy()

def main():
    """Main entry point for setup"""
    setup = CloudSyncSetup()
    setup.run()

if __name__ == "__main__":
    main()
