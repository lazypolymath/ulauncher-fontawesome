#!/usr/bin/env python3
import os
import re
import json
import requests
from pathlib import Path
import shutil

from svg_helper import modify_svg_color

# Configuration
EXTENSION_DIR = Path(__file__).parent
DATA_DIR = EXTENSION_DIR / "data"
ICONS_DIR = EXTENSION_DIR / "images" / "icons"
FONTAWESOME_API_URL = "https://api.fontawesome.com/releases/latest-icons.json"
FONTAWESOME_SVG_BASE_URL = "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs"

DEFAULT_ICON_COLOR = '#7dcfff'

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
ICONS_DIR.mkdir(exist_ok=True, parents=True)

def download_fontawesome_data():
    """Download and process FontAwesome icon data"""
    print("Downloading FontAwesome metadata...")
    
    # For this example, we'll use a local approach instead of the API which requires authentication
    # First try to download from the official repository
    try:
        response = requests.get("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/metadata/icons.json")
        if response.status_code == 200:
            raw_data = response.json()
            print(f"Successfully downloaded data for {len(raw_data)} icons")
            return raw_data
    except Exception as e:
        print(f"Error downloading from GitHub: {e}")
    
    # Fallback to a simplified approach
    print("Using fallback method to generate icons data")
    # Here we'll use a hardcoded list of common icons
    common_icons = {
        "address-book": ["contact", "directory", "index", "little black book"],
        "bell": ["alarm", "alert", "chime", "notification", "reminder"],
        "calendar": ["date", "event", "schedule", "time", "when"],
        "heart": ["favorite", "like", "love", "relationship", "valentine"],
        "home": ["abode", "building", "house", "main"],
        "search": ["find", "lookup", "magnifying glass", "explore"],
        "user": ["account", "avatar", "head", "human", "profile", "person"],
        "cog": ["gear", "mechanical", "settings", "sprocket", "wheel"],
        "envelope": ["e-mail", "email", "letter", "mail", "message"],
        "star": ["award", "favorite", "rating", "score"],
        "code": ["brackets", "development", "html", "programming"],
        "github": ["octocat", "social network", "version control"],
        "twitter": ["social network", "tweet", "bird"],
        "facebook": ["social network", "facebook-official"],
        "google": ["search", "search engine"]
    }
    
    # Create a simplified dataset
    icons_data = {}
    for icon_name, search_terms in common_icons.items():
        icons_data[icon_name] = {
            "id": icon_name,
            "styles": ["solid"],
            "unicode": "",  # Placeholder
            "search_terms": search_terms
        }
        
        # Add brands style for brand icons
        if icon_name in ["github", "twitter", "facebook", "google"]:
            icons_data[icon_name]["styles"] = ["brands"]
            
        # Add regular style option for some icons
        if icon_name in ["address-book", "bell", "heart", "user", "envelope", "star"]:
            icons_data[icon_name]["styles"] = ["solid", "regular"]
    
    return icons_data

def create_fontawesome_json(icons_data):
    """Create a properly formatted JSON file for the extension"""
    output_file = DATA_DIR / "fontawesome.json"
    
    # Format the data for our extension
    formatted_data = {}
    for icon_name, icon_data in icons_data.items():
        # If using official data
        if isinstance(icon_data, dict) and "label" in icon_data:
            formatted_data[icon_name] = {
                "id": icon_name,
                "styles": icon_data.get("styles", []),
                "unicode": icon_data.get("unicode", ""),
                "search_terms": icon_data.get("search", {}).get("terms", [])
            }
        else:
            # Our fallback data is already in the right format
            formatted_data[icon_name] = icon_data
    
    # Write the JSON file
    with open(output_file, 'w') as f:
        json.dump(formatted_data, f, indent=2)
    
    print(f"Created FontAwesome JSON file at {output_file} with {len(formatted_data)} icons")
    return formatted_data

def download_svg_icons(icons_data):
    """Download SVG icons for each icon in the data"""
    print(f"Downloading SVG icons to {ICONS_DIR}...")
    downloaded = 0
    
    for icon_name, icon_data in icons_data.items():
        styles = icon_data.get("styles", ["solid"])
        
        # Try to download each style variant
        for style in styles:
            style_dir = "brands" if style == "brands" else style
            svg_url = f"{FONTAWESOME_SVG_BASE_URL}/{style_dir}/{icon_name}.svg"

            try:
                svg_response = requests.get(svg_url)
                if svg_response.status_code == 200:
                    svg_path = ICONS_DIR / f"{icon_name}.svg"
                    with open(svg_path, 'wb') as f:
                        f.write(svg_response.content)
                    
                    modify_svg_color(svg_path, DEFAULT_ICON_COLOR)
                    
                    downloaded += 1
                    break  # Only need one SVG per icon
            except Exception as e:
                # Just continue if we can't download this icon
                pass
    
    print(f"Downloaded and processed {downloaded} SVG icons.")

def create_default_icon():
    """Create a default icon if none exists"""
    default_icon_path = EXTENSION_DIR / "images" / "icon.png"
    
    # Create images directory if it doesn't exist
    (EXTENSION_DIR / "images").mkdir(exist_ok=True, parents=True)
    
    if not default_icon_path.exists():
        print("Creating default icon...")
        # Create a simple default icon (a blue square in this case)
        try:
            # Try to use an existing FontAwesome icon as the default
            for icon_file in ICONS_DIR.glob("font-awesome.svg"):
                shutil.copy(icon_file, default_icon_path.with_suffix(".svg"))
                modify_svg_color(icon_file, DEFAULT_ICON_COLOR)
                print(f"Created default icon at {default_icon_path.with_suffix('.svg')}")
                break
        except Exception:
            # Just notify if we couldn't create a default icon
            print("Could not create a default icon. Please add an icon.png file to the images directory.")

def main():
    print("Setting up FontAwesome icons for your Ulauncher extension...")
    
    # Get FontAwesome data
    icons_data = download_fontawesome_data()
    
    # Create the JSON file
    formatted_data = create_fontawesome_json(icons_data)
    
    # Download SVG icons
    download_svg_icons(formatted_data)
    
    # Create default icon
    create_default_icon()
    
    print("Setup complete! Your FontAwesome extension is ready to use.")

if __name__ == "__main__":
    main()
