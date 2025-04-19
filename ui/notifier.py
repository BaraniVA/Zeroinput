import os
import platform
from datetime import datetime

class Notifier:
    def __init__(self):
        self.last_notification_time = None
        self.notification_cooldown = 30  # seconds between notifications
        self.system = "Console"  # Default to console
        self.setup_notifier()
        
    def setup_notifier(self):
        """Setup platform-specific notification system"""
        try:
            self.system = platform.system()
            print(f"Setting up notifier for {self.system}")
            
            if self.system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    self.toaster = ToastNotifier()
                    print("✅ Windows notification system initialized")
                except ImportError:
                    print("⚠️ win10toast not installed, falling back to console notifications")
                    self.system = "Console"
                except Exception as e:
                    print(f"⚠️ Error initializing Windows notifications: {e}")
                    self.system = "Console"
        except Exception as e:
            print(f"❌ Failed to initialize notification system: {e}")
            self.system = "Console"
    
    def send_notification(self, title, message, icon=None):
        """Send a notification with cooldown management"""
        now = datetime.now()
        
        # Check if we should show this notification (cooldown)
        if self.last_notification_time:
            time_diff = (now - self.last_notification_time).total_seconds()
            if time_diff < self.notification_cooldown:
                print(f"Notification cooldown ({time_diff:.1f}s < {self.notification_cooldown}s)")
                return False
        
        self.last_notification_time = now
        
        # Send platform-specific notification
        try:
            if self.system == "Windows":
                try:
                    self.toaster.show_toast(
                        title,
                        message,
                        duration=5,
                        threaded=True
                    )
                except Exception as e:
                    print(f"Windows notification error: {e}")
                    print(f"\n📣 {title}: {message}")
            elif self.system == "Console":
                print(f"\n📣 {title}: {message}")
            
            return True
        except Exception as e:
            print(f"Error sending notification: {e}")
            print(f"📣 {title}: {message}")
            return False

# Singleton instance
notifier = Notifier()

def show_suggestion(suggestion):
    """Show a suggestion notification"""
    try:
        notifier.send_notification(
            "ZeroInput Suggestion 💡",
            suggestion
        )
    except Exception as e:
        print(f"Error in show_suggestion: {e}")
        print(f"💡 {suggestion}")

def show_error(message):
    """Show an error notification"""
    try:
        notifier.send_notification(
            "ZeroInput Error ❌",
            message
        )
    except Exception as e:
        print(f"Error in show_error: {e}")
        print(f"❌ {message}")

def show_status(message):
    """Show a status notification"""
    try:
        notifier.send_notification(
            "ZeroInput Status 📊",
            message
        )
    except Exception as e:
        print(f"Error in show_status: {e}")
        print(f"📊 {message}")