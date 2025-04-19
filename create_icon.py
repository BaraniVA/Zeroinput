from PIL import Image, ImageDraw
import os

def create_icon():
    """Create a simple icon for ZeroInput"""
    # Create a solid color background (better compatibility)
    size = 64
    image = Image.new('RGB', (size, size), (52, 152, 219))  # Blue background
    draw = ImageDraw.Draw(image)
    
    # Draw a simple design - just text
    draw.text((size//2-10, size//2-10), "ZI", fill=(255, 255, 255))
    
    # Ensure assets directory exists
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    # Save as PNG
    icon_path = os.path.join(assets_dir, "zeroinput_icon.png")
    image.save(icon_path)
    print(f"Icon saved to {icon_path}")
    
    return icon_path

if __name__ == "__main__":
    create_icon()