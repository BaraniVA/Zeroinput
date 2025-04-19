from agent.integration import run_complete_cycle, synchronize_components
import time
import sys
import os
import traceback
import platform
import subprocess

# Create assets directory if it doesn't exist
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")
    
    # Check if Ollama is installed and running
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2
        )
        if result.returncode == 0:
            print("✅ Ollama is installed and running")
        else:
            print("⚠️ Ollama is installed but may not be running correctly")
    except FileNotFoundError:
        print("❌ Ollama is not installed or not in PATH. Suggestions will use fallback methods.")
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
    
    # Check for other dependencies as needed
    try:
        import pystray
        print("✅ Pystray module is available")
    except ImportError:
        print("❌ Pystray module is missing. Install with: pip install pystray")
    
    try:
        from PIL import Image
        print("✅ PIL module is available")
    except ImportError:
        print("❌ PIL module is missing. Install with: pip install Pillow")
    
    print("Dependency check complete.")
    print()

def main():
    print("🚀 Starting ZeroInput System")
    
    # Create icon if it doesn't exist
    icon_path = os.path.join(assets_dir, "zeroinput_icon.png")
    if not os.path.exists(icon_path):
        try:
            from create_icon import create_icon
            create_icon()
        except Exception as e:
            print(f"Warning: Could not create icon: {e}")
    
    # Initialize UI components
    tray = None
    try:
        from ui.notifier import show_status
        show_status("ZeroInput has started")
        
        try:
            from ui.tray import initialize_tray
            tray = initialize_tray()
        except Exception as e:
            print(f"Warning: Could not initialize tray: {e}")
    except Exception as e:
        print(f"Warning: UI initialization error: {e}")
    
    # Initial synchronization
    print("Performing initial synchronization...")
    try:
        synchronize_components()
    except Exception as e:
        print(f"Warning: Synchronization error: {e}")
    
    # Run continuous monitoring
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n=== Cycle {cycle_count} ===")
            
            try:
                suggestion = run_complete_cycle()
                print(f"💡 Suggestion: {suggestion}")
                
                # Update UI with suggestion
                try:
                    from ui.notifier import show_suggestion
                    show_suggestion(suggestion)
                except Exception as e:
                    print(f"Warning: Notification error: {e}")
                
                # Update tray with suggestion
                if tray:
                    try:
                        tray.update_suggestion(suggestion)
                    except Exception as e:
                        print(f"Warning: Tray update error: {e}")
            except Exception as e:
                print(f"Error in cycle {cycle_count}: {e}")
            
            print(f"Waiting for next cycle...")
            time.sleep(10)  # Wait 10 seconds between cycles
            
    except KeyboardInterrupt:
        print("\n🛑 ZeroInput system stopped by user")
    except Exception as e:
        print("\n❌ Error in ZeroInput system:")
        traceback.print_exc()
        try:
            from ui.notifier import show_error
            show_error(str(e))
        except:
            pass
    
    print("Goodbye! 👋")

if __name__ == "__main__":
    main()