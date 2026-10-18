"""
post_processor.py - Image Post-Processing and Customization

This module provides post-processing capabilities for generated ad images:
    - Text overlay (headline, tagline, call-to-action button)
    - Logo placement with configurable position and scale
    - Image adjustments (brightness, contrast, saturation, blur)
    - Resize/crop for specific platform dimensions

All operations use the Pillow (PIL) library for image manipulation.
"""

import os
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


def get_font(size, bold=False):
    """
    Attempt to load a system font, falling back to PIL's default font.

    Tries multiple common font paths across macOS and Linux systems.
    If no system font is found, returns PIL's built-in bitmap font.

    Args:
        size (int): Desired font size in pixels.
        bold (bool): Whether to prefer a bold font variant.

    Returns:
        PIL.ImageFont: A font object suitable for text rendering.
    """
    # List of common font paths on macOS and Linux
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",           # macOS
        "/System/Library/Fonts/HelveticaNeue.ttc",       # macOS bold
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux bold
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    # Try each font path until one works
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue

    # Fallback to PIL's default bitmap font
    print("  [WARN] No system fonts found, using default font")
    return ImageFont.load_default()


def add_text_overlay(image_path, headline="", tagline="", cta_text="",
                     text_color="#FFFFFF", text_position="bottom",
                     overlay_opacity=0.5):
    """
    Add a text overlay to an advertisement image.

    Creates a semi-transparent band on the image and renders text elements:
    headline (large, bold), tagline (medium), and a CTA button (with background).

    Args:
        image_path (str): Path to the source image file.
        headline (str): Main headline text (large, bold).
        tagline (str): Supporting tagline text (medium size).
        cta_text (str): Call-to-action button text (e.g., "Shop Now").
        text_color (str): Hex color code for text (default: white).
        text_position (str): "top", "center", or "bottom" placement.
        overlay_opacity (float): Opacity of the dark band behind text (0.0-1.0).

    Returns:
        PIL.Image.Image: The image with text overlay applied.
    """
    # Open the image and convert to RGBA for alpha compositing
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    # Create a transparent overlay layer for the text band
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Calculate the position and height of the text band
    band_h = int(h * 0.35)  # Band covers 35% of image height
    if text_position == "top":
        band_y = 0
    elif text_position == "center":
        band_y = (h - band_h) // 2
    else:  # bottom (default)
        band_y = h - band_h

    # Draw semi-transparent dark band behind the text
    alpha = int(255 * overlay_opacity)
    draw.rectangle([0, band_y, w, band_y + band_h], fill=(0, 0, 0, alpha))

    # Parse the hex color string to RGBA tuple
    hex_color = text_color.lstrip("#")
    color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

    # Starting Y position for text rendering (10% padding from band top)
    y_cursor = band_y + int(band_h * 0.1)

    # Render the headline text (large, bold, centered)
    if headline:
        font_size = max(16, int(h * 0.06))
        font = get_font(font_size, bold=True)
        bbox = draw.textbbox((0, 0), headline, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2  # Center horizontally
        draw.text((x, y_cursor), headline, fill=color, font=font)
        y_cursor += int(font_size * 1.4)  # Move cursor down

    # Render the tagline text (medium size, centered)
    if tagline:
        font_size = max(12, int(h * 0.035))
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), tagline, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y_cursor), tagline, fill=color, font=font)
        y_cursor += int(font_size * 1.6)

    # Render the CTA button (text with rounded rectangle background)
    if cta_text:
        font_size = max(14, int(h * 0.04))
        font = get_font(font_size, bold=True)
        bbox = draw.textbbox((0, 0), cta_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Calculate button dimensions with padding
        btn_w = tw + int(font_size * 2)
        btn_h = th + int(font_size * 0.8)
        btn_x = (w - btn_w) // 2
        btn_y = y_cursor + int(font_size * 0.3)

        # Draw rounded rectangle button background
        draw.rounded_rectangle(
            [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
            radius=int(btn_h * 0.3),
            fill=color,
        )

        # Draw button text in contrasting color (black on white button)
        text_x = btn_x + (btn_w - tw) // 2
        text_y = btn_y + (btn_h - th) // 2
        draw.text((text_x, text_y), cta_text, fill=(0, 0, 0, 255), font=font)

    # Composite the overlay onto the original image
    result = Image.alpha_composite(img, overlay).convert("RGB")
    return result


def add_logo(image_path, logo_path, position="top-right", scale=0.15):
    """
    Add a logo image to the advertisement.

    The logo is resized proportionally based on the scale parameter
    and placed at the specified corner position with padding.

    Args:
        image_path (str): Path to the source advertisement image.
        logo_path (str): Path to the logo image file (PNG with transparency preferred).
        position (str): Placement position - "top-left", "top-right",
                       "bottom-left", "bottom-right", or "center".
        scale (float): Logo size relative to image width (0.05-0.4).

    Returns:
        PIL.Image.Image: The image with logo added.
    """
    # Open both images with alpha channel support
    img = Image.open(image_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    w, h = img.size

    # Resize logo proportionally based on scale factor
    logo_w = int(w * scale)
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

    # Calculate position with 3% padding from edges
    padding = int(w * 0.03)
    positions = {
        "top-left": (padding, padding),
        "top-right": (w - logo_w - padding, padding),
        "bottom-left": (padding, h - logo_h - padding),
        "bottom-right": (w - logo_w - padding, h - logo_h - padding),
        "center": ((w - logo_w) // 2, (h - logo_h) // 2),
    }
    pos = positions.get(position, positions["top-right"])

    # Paste logo onto the image using alpha channel as mask
    img.paste(logo, pos, logo)
    return img.convert("RGB")


def adjust_image(image_path, brightness=1.0, contrast=1.0,
                 saturation=1.0, blur=0.0):
    """
    Apply image adjustments for fine-tuning the advertisement visual.

    Uses PIL's ImageEnhance module for brightness, contrast, and saturation,
    and ImageFilter for Gaussian blur.

    Args:
        image_path (str): Path to the source image file.
        brightness (float): Brightness factor (1.0 = original, >1 brighter).
        contrast (float): Contrast factor (1.0 = original, >1 more contrast).
        saturation (float): Color saturation factor (1.0 = original, 0 = grayscale).
        blur (float): Gaussian blur radius (0 = no blur).

    Returns:
        PIL.Image.Image: The adjusted image.
    """
    img = Image.open(image_path).convert("RGB")

    # Apply brightness adjustment
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
        print("  Applied brightness: {}".format(brightness))

    # Apply contrast adjustment
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
        print("  Applied contrast: {}".format(contrast))

    # Apply color saturation adjustment
    if saturation != 1.0:
        img = ImageEnhance.Color(img).enhance(saturation)
        print("  Applied saturation: {}".format(saturation))

    # Apply Gaussian blur if specified
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        print("  Applied blur: {}".format(blur))

    return img


def resize_image(image_path, width, height):
    """
    Resize an image to specific dimensions for platform export.

    Uses LANCZOS resampling for high-quality downscaling.

    Args:
        image_path (str): Path to the source image file.
        width (int): Target width in pixels.
        height (int): Target height in pixels.

    Returns:
        PIL.Image.Image: The resized image.
    """
    img = Image.open(image_path).convert("RGB")
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    print("  Resized to {}x{}".format(width, height))
    return resized
