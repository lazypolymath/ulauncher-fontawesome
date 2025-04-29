import logging
import os
import re

logger = logging.getLogger(__name__)

def update_svg_colors(color, base_dir):
    """Update SVG colors for better visibility"""
    images_dir = os.path.join(base_dir, 'images')
    icons_dir = os.path.join(images_dir, 'icons')

    # Set the default icon color
    modify_svg_color(os.path.join(images_dir, 'icon.svg'), color)
    
    try:
        for svg_file in os.listdir(icons_dir):
            if svg_file.endswith('.svg'):
                svg_path = os.path.join(icons_dir, svg_file)
                modify_svg_color(svg_path, color)
    except Exception as e:
        logger.error(f"Error updating SVG colors: {e}")

def modify_svg_color(svg_path, color):
    """Modify SVG to have a specific color"""
    try:
        if not os.path.exists(svg_path):
            logger.warning(f"SVG file does not exist: {svg_path}")
            return False

        with open(svg_path, 'r') as file:
            svg_content = file.read()
            
        # Add fill attribute to the svg tag or replace existing fill
        if '<svg' in svg_content:
            if 'fill=' not in svg_content:
                svg_content = svg_content.replace('<svg', f'<svg fill="{color}"')
            else:
                svg_content = re.sub(r'fill="[^"]*"', f'fill="{color}"', svg_content)
            
            # Write the modified content back
            with open(svg_path, 'w') as file:
                file.write(svg_content)
                
            return True
        else:
            logger.warning(f"Invalid SVG file: {svg_path}")
            return False
    except Exception as e:
        logger.error(f"Error modifying SVG color: {e}")
        return False
