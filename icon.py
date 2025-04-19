import os
from PIL import Image

# Define the path to your PNG icon
# Option 1: If it's in the project root directory
project_dir = os.path.dirname(os.path.abspath(__file__))
png_path = os.path.join(project_dir, 'assets', 'zeroinput_icon.png')

# Option 2: If it's in an assets directory
# png_path = os.path.join(project_dir, 'assets', 'zeroinput_icon.png')

# Check if the file exists at this path
if not os.path.exists(png_path):
    print(f"Error: Could not find icon file at {png_path}")
    print("Please specify the correct path to zeroinput_icon.png")
    exit(1)
    
print(f"Found icon at: {png_path}")

# Create assets directory if it doesn't exist
assets_dir = os.path.join(project_dir, "assets")
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

# Convert PNG to ICO
img = Image.open(png_path)
icon_path = os.path.join(assets_dir, 'icon.ico')
img.save(icon_path, format='ICO')

print(f"Successfully created icon at: {icon_path}")
print(f"Now run: pyinstaller --onefile --windowed --icon={icon_path} --name=ZeroInput main.py")