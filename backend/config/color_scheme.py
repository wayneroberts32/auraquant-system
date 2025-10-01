"""
AuraQuant Color Scheme Configuration
=====================================
CRITICAL: These colors are LOCKED and must never be changed.
This file defines the official AuraQuant color palette for all UI components.

Created: 2025-01-30
Status: PRODUCTION-LOCKED
"""

# AuraQuant Official Color Scheme - IMMUTABLE
AURAQUANT_COLORS = {
    # Primary Colors
    "background": "#131722",        # Dark background from trading terminals
    "panel": "#1e222d",             # Panel background color
    "success": "#00ff88",           # Green for profits/success
    "danger": "#ff4444",            # Red for losses/warnings
    "text": "#d1d4dc",              # Primary text color
    
    # Secondary Colors (extracted from help-centre.html)
    "cyan": "#00ffff",              # Accent cyan
    "purple": "#ff00ff",            # Accent purple
    "border_cyan": "rgba(0, 255, 255, 0.3)",  # Border color
    "border_green": "rgba(0, 255, 136, 0.3)",  # Success border
    
    # Gradient Backgrounds
    "gradient_primary": "linear-gradient(135deg, #0a0a0a 0%, #1a0033 50%, #000510 100%)",
    "gradient_feature": "linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(255, 0, 255, 0.1))",
    "gradient_text": "linear-gradient(90deg, #00ff88, #00ffff, #ff00ff)",
    
    # Transparency Variants
    "panel_transparent": "rgba(0, 0, 0, 0.6)",
    "panel_heavy": "rgba(0, 0, 0, 0.8)",
    "highlight": "rgba(0, 255, 255, 0.1)",
    "active": "rgba(0, 255, 255, 0.2)",
    
    # Status Colors
    "online": "#00ff88",            # System online
    "offline": "#ff4444",           # System offline
    "warning": "#ffaa00",           # Warning state
    "info": "#00aaff",              # Information
}

# Logo Configuration
LOGO_CONFIG = {
    "path": "frontend/Logo/Logo With AuraQuant.png",
    "animation": "rotate 10s linear infinite",  # Slow spin animation
    "size": {
        "header": "50px",
        "dashboard": "40px",
        "login": "80px"
    }
}

# Typography
TYPOGRAPHY = {
    "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "font_mono": "'Courier New', monospace",
    "font_sizes": {
        "title": "28px",
        "heading": "24px",
        "subheading": "18px",
        "body": "16px",
        "small": "14px",
        "tiny": "12px"
    },
    "font_weights": {
        "bold": 700,
        "semibold": 600,
        "regular": 400,
        "light": 300
    }
}

# Animation Timings
ANIMATIONS = {
    "transition_fast": "0.2s ease",
    "transition_normal": "0.3s ease",
    "transition_slow": "0.5s ease",
    "logo_spin": "10s linear infinite",
    "pulse": "2s ease-in-out infinite",
}

# Layout Constants
LAYOUT = {
    "sidebar_width": "280px",
    "header_height": "70px",
    "border_radius": {
        "small": "5px",
        "medium": "10px",
        "large": "25px",
    },
    "spacing": {
        "xs": "5px",
        "sm": "10px",
        "md": "15px",
        "lg": "20px",
        "xl": "30px",
    }
}

def get_css_variables():
    """Generate CSS custom properties for use in stylesheets"""
    css_vars = []
    for key, value in AURAQUANT_COLORS.items():
        css_key = f"--auraquant-{key.replace('_', '-')}"
        css_vars.append(f"{css_key}: {value};")
    return "\n".join(css_vars)

def validate_color(color_key):
    """Validate if a color key exists in the official scheme"""
    return color_key in AURAQUANT_COLORS

def get_color(color_key, default="#ffffff"):
    """Safely get a color value with fallback"""
    return AURAQUANT_COLORS.get(color_key, default)

# Export for JavaScript/Frontend
def export_to_json():
    """Export color scheme as JSON for frontend consumption"""
    import json
    return json.dumps({
        "colors": AURAQUANT_COLORS,
        "logo": LOGO_CONFIG,
        "typography": TYPOGRAPHY,
        "animations": ANIMATIONS,
        "layout": LAYOUT
    }, indent=2)

# Validation check
if __name__ == "__main__":
    print("AuraQuant Color Scheme - LOCKED Configuration")
    print("=" * 50)
    print(f"Total Colors Defined: {len(AURAQUANT_COLORS)}")
    print(f"Logo Path: {LOGO_CONFIG['path']}")
    print("\nPrimary Colors:")
    for key in ["background", "panel", "success", "danger", "text"]:
        print(f"  {key}: {AURAQUANT_COLORS[key]}")