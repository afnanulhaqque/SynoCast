import os
from PIL import Image

def make_square(image_path, size, output_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGBA")
        
        # Calculate aspect ratio preserving resize
        ratio = min(size[0] / img.width, size[1] / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create new square canvas
        new_img = Image.new("RGBA", size, (0, 0, 0, 0))
        
        # Paste centered
        x = (size[0] - new_size[0]) // 2
        y = (size[1] - new_size[1]) // 2
        new_img.paste(img, (x, y))
        
        new_img.save(output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Error creating {output_path}: {e}")

# Sources
logo_path = 'd:/SynoCast/assets/logo/logo.png' 
# Use logo.png as source as it is higher res
   
# Targets
make_square(logo_path, (192, 192), 'd:/SynoCast/assets/logo/icon-192.png')
make_square(logo_path, (512, 512), 'd:/SynoCast/assets/logo/icon-512.png')
