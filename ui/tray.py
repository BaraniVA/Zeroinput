import os
import sys
import threading
import pystray
from PIL import Image, ImageDraw
from datetime import datetime

class ZeroInputTray:
    def __init__(self):
        self.running = True
        self.monitoring = True
        self.last_suggestion = "No suggestions yet"
        self.suggestion_time = None
        self.icon = None
        self.create_icon()
        
    def create_icon(self):
        """Create the system tray icon"""
        try:
            # Try to load the icon image
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "zeroinput_icon.png")
            
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
            else:
                # Create a simple icon if image not found
                image = self.create_default_icon()
                
            # Create a simplified menu
            self.icon = pystray.Icon(
                "zeroinput",
                image,
                "ZeroInput"
            )
            
            # Set the menu after creation
            self.icon.menu = self.get_menu()
            
            return True
        except Exception as e:
            print(f"Error creating tray icon: {e}")
            return False
    
    def get_menu(self):
        """Get the current menu - called dynamically when menu is shown"""
        return pystray.Menu(
            pystray.MenuItem("ZeroInput", None, enabled=False),
            pystray.MenuItem(f"Last: {self.last_suggestion[:25]}..." if len(self.last_suggestion) > 25 else f"Last: {self.last_suggestion}", 
                            self.show_last_suggestion),
            pystray.MenuItem("Toggle Monitoring", self.toggle_monitoring, 
                            checked=lambda _: self.monitoring),
            pystray.MenuItem("Exit", self.exit_app)
        )
    
    def create_default_icon(self, size=64):
        """Create a default icon if no image is available"""
        image = Image.new('RGB', (size, size), (52, 152, 219))
        draw = ImageDraw.Draw(image)
        
        # Draw "ZI" in the middle (simple white text)
        draw.text((size//2-10, size//2-15), "ZI", fill=(255, 255, 255))
        
        return image
    
    def update_suggestion(self, suggestion):
        """Update the last suggestion"""
        self.last_suggestion = suggestion
        self.suggestion_time = datetime.now()
    
    def show_last_suggestion(self, icon, item):
        """Display the last suggestion"""
        time_str = self.suggestion_time.strftime("%H:%M:%S") if self.suggestion_time else "Unknown"
        message = f"[{time_str}] {self.last_suggestion}"
        print(f"\n📱 Last suggestion: {message}")
        
        # Use notifier to show the suggestion
        try:
            from ui.notifier import show_suggestion
            show_suggestion(message)
        except Exception as e:
            print(f"Error showing suggestion: {e}")
    
    def toggle_monitoring(self, icon, item):
        """Toggle the monitoring state"""
        self.monitoring = not self.monitoring
        status = "enabled" if self.monitoring else "disabled"
        print(f"Monitoring {status}")
        
    def exit_app(self, icon, item):
        """Exit the application"""
        print("Exiting ZeroInput via tray...")
        icon.stop()
        self.running = False
        os._exit(0)  # Force exit
    
    def run(self):
        """Run the system tray icon"""
        if self.icon:
            try:
                self.icon.run()
            except Exception as e:
                print(f"Error running tray icon: {e}")

# Initialize tray without a global variable
def initialize_tray():
    """Initialize the system tray icon in a separate thread"""
    try:
        tray = ZeroInputTray()
        
        # Start the tray in a separate thread
        tray_thread = threading.Thread(target=tray.run, daemon=True)
        tray_thread.start()
        
        return tray
    except Exception as e:
        print(f"Error initializing tray: {e}")
        return None

def update_suggestion(suggestion):
    """Update the suggestion in the tray"""
    global tray
    if tray:
        tray.update_suggestion(suggestion)