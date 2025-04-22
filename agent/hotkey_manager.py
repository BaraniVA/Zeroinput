import keyboard
import threading
import time
from typing import Callable, Dict, Any

class HotkeyManager:
    def __init__(self):
        self.current_suggestion = None
        self.action_callback = None
        self.is_listening = False
        self.listener_thread = None
    
    def set_action_callback(self, callback: Callable[[Dict[str, Any]], bool]):
        """Set callback function to execute when hotkey is pressed"""
        self.action_callback = callback
    
    def update_current_suggestion(self, suggestion: str):
        """Update the current suggestion"""
        self.current_suggestion = suggestion
    
    def start_listening(self):
        """Start listening for hotkeys"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        # Register the global hotkey
        keyboard.add_hotkey('alt+y', self._hotkey_callback)
        
        # Start a background thread to keep listening
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()
        
        print("Hotkey listening started (Alt+Y to accept suggestions)")
    
    def stop_listening(self):
        """Stop listening for hotkeys"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        # Unregister the hotkey
        try:
            keyboard.remove_hotkey('alt+y')
        except:
            pass
        
        # The thread will terminate on its own since it's a daemon thread
        print("Hotkey listening stopped")
    
    def _hotkey_callback(self):
        """Called when the hotkey is pressed"""
        if not self.current_suggestion or not self.action_callback:
            print("No current suggestion to execute")
            return
        
        # Import here to avoid circular imports
        from agent.action_executor import extract_action_from_suggestion
        
        # Extract action from the current suggestion
        action_info = extract_action_from_suggestion(self.current_suggestion)
        
        # Execute the action
        if self.action_callback:
            result = self.action_callback(action_info)
            
            if result['info_only']:
                print(f"ℹ️ Information only: {result['message']}")
            elif result['success']:
                print(f"✅ Successfully executed suggestion: {self.current_suggestion}")
            else:
                print(f"❌ Failed to execute suggestion: {self.current_suggestion}")
    
    def _listener_loop(self):
        """Background thread to keep listening for keyboard events"""
        while self.is_listening:
            time.sleep(0.1)  # Reduce CPU usage