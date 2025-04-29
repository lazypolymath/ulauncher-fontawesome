import json
import logging
import os
from functools import lru_cache
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesUpdateEvent, PreferencesEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

from svg_helper import update_svg_colors

logger = logging.getLogger(__name__)

FONTAWESOME_ICONS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'fontawesome.json')

DEFAULT_COPY_FORMAT = 'html'
DEFAULT_ICON_COLOR = '#7dcfff'

class FontAwesomeSearchExtension(Extension):
    def __init__(self):
        logger.debug('Initializing FontAwesome Search Extension')
        super(FontAwesomeSearchExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        
        # Default preferences
        self.copy_format = DEFAULT_COPY_FORMAT
        self.icon_color = DEFAULT_ICON_COLOR
        
        # Load FontAwesome icons data
        self.icons_data = self._load_icons_data()
        
    def _load_icons_data(self):
        """Load FontAwesome icons data from JSON file"""
        try:
            with open(FONTAWESOME_ICONS_FILE, 'r') as f:
                icons_data = json.load(f)
                logger.debug(f"Loaded {len(icons_data)} FontAwesome icons")
                return icons_data
        except Exception as e:
            logger.error(f"Error loading FontAwesome icons: {e}")
            return {}


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        extension.copy_format = event.preferences.get("copy_format", DEFAULT_COPY_FORMAT)
        extension.icon_color = event.preferences.get("icon_color", DEFAULT_ICON_COLOR)
        extension.max_results = int(extension.preferences.get("max_results", 10))
        
        # Update SVG colors if icon color changed
        update_svg_colors(extension.icon_color, os.path.dirname(__file__))


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        if event.id == "copy_format":
            extension.copy_format = event.new_value
        elif event.id == "icon_color":
            extension.icon_color = event.new_value
            # Update SVG colors when icon color changes
            update_svg_colors(extension.icon_color, os.path.dirname(__file__))


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        query = event.get_argument() or ""
        
        if not query:
            # Show instructions if no query provided
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.svg',
                    name="Search FontAwesome Icons",
                    description="Type to search FontAwesome icons by name",
                    on_enter=HideWindowAction()
                )
            ])
        
        # Search through icons
        matched_icons = self._search_icons(query, extension.icons_data)
        
        # Create result items
        items = self._create_results(matched_icons, extension)
        
        if not items:
            items.append(ExtensionResultItem(
                icon='images/icon.svg',
                name="No matching icons found",
                description=f"No FontAwesome icons match '{query}'",
                on_enter=HideWindowAction()
            ))
            
        return RenderResultListAction(items)
    
    def _search_icons(self, query, icons_data):
        """Search for icons matching the query"""
        query = query.lower()
        matched_icons = []
        
        for icon_name, icon_data in icons_data.items():
            # Check if query matches icon name or search terms
            if (query in icon_name.lower() or 
                any(query in tag.lower() for tag in icon_data.get("search_terms", []))):
                matched_icons.append((icon_name, icon_data))
        
        # Sort results by relevance
        matched_icons.sort(key=lambda x: (
            0 if x[0].lower() == query else 
            1 if x[0].lower().startswith(query) else 
            2 if query in x[0].lower() else
            3  # For matches in search terms only
        ))

        # Limit results to 10
        return matched_icons[:10]
    
    def _create_results(self, matched_icons, extension):
        """Create result items from matched icons"""
        base_dir = os.path.dirname(__file__)
        items = []
        
        for icon_name, icon_data in matched_icons:
            icon_id = icon_data.get('id', icon_name)
            icon_path = os.path.join(base_dir, "images", "icons", f"{icon_id}.svg")
            fallback_icon = os.path.join(base_dir, "images", "icon.svg")
            
            # Get style info
            styles = icon_data.get('styles', ['solid'])
            style = styles[0] if styles else 'solid'
            
            # Get unicode value
            unicode_value = icon_data.get('unicode', '')
            
            # Generate copy content based on format preference (primary format)
            copy_content = get_copy_content(
                extension.copy_format, 
                icon_name, 
                icon_id, 
                unicode_value, 
                style, 
                base_dir
            )
            
            # Limit displayed search terms for better readability
            search_terms_part = ""
            if icon_data.get('search_terms'):
                terms = icon_data.get('search_terms', [])[:5]
                if terms:
                    search_terms_part = f" - {', '.join(terms)}"

            # Create description with style information
            style_display = style.capitalize()
            description = f"FontAwesome {style_display} icon{search_terms_part}"

            items.append(ExtensionResultItem(
                icon=icon_path if os.path.exists(icon_path) else fallback_icon,
                name=f"{icon_name}",
                description=description,
                on_enter=CopyToClipboardAction(copy_content),
            ))
        
        return items


@lru_cache(maxsize=64)
def get_copy_content(format_type, icon_name, icon_id, unicode_value, style, base_dir):
    """Generate copy content based on the selected format with caching for performance"""
    style_short = 's' if style == 'solid' else ('r' if style == 'regular' else 'b')
    
    if format_type == "html":
        return f'<i class="fa{style_short} fa-{icon_name}"></i>'
    elif format_type == "class":
        return f'fa{style_short} fa-{icon_name}'
    elif format_type == "unicode":
        return f'&#{unicode_value};' if unicode_value else f'fa{style_short} fa-{icon_name}'
    elif format_type == "svg":
        # Read and return the actual SVG content
        svg_path = os.path.join(base_dir, "images", "icons", f"{icon_id}.svg")
        try:
            if os.path.exists(svg_path):
                with open(svg_path, 'r') as f:
                    return f.read()
            else:
                return f'<i class="fa{style_short} fa-{icon_name}"></i>'  # Fallback to HTML
        except Exception as e:
            logger.error(f"Error reading SVG file: {e}")
            return f'<i class="fa{style_short} fa-{icon_name}"></i>'  # Fallback to HTML
    else:
        return f'<i class="fa{style_short} fa-{icon_name}"></i>'  # Default to HTML


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        return HideWindowAction()


if __name__ == '__main__':
    logger.debug('Starting FontAwesome Search Extension')
    FontAwesomeSearchExtension().run()
