"""
exporter.py - Image Export and Format Conversion

This module handles exporting generated advertisement images in multiple
formats (PNG, JPEG, WebP) with configurable quality settings. It also
provides platform-specific export presets that automatically resize and
optimize images for different ad platforms (Instagram, Facebook, etc.).

Supported Export Formats:
    - PNG: Lossless compression, best quality, larger file size
    - JPEG: Lossy compression, smaller files, good for web
    - WebP: Modern format, efficient compression, wide browser support
"""

import os
import io
from PIL import Image

from config import OUTPUT_DIR, PLATFORM_PRESETS, EXPORT_FORMATS


def export_image(image_path, fmt="png", quality=90, output_filename=None):
    """
    Export an image in the specified format with quality settings.

    Converts the image to the target format and saves it to the output
    directory. Handles format-specific options like JPEG optimization
    and WebP quality settings.

    Args:
        image_path (str): Path to the source image file.
        fmt (str): Target format - "png", "jpg"/"jpeg", or "webp".
        quality (int): Compression quality for JPEG/WebP (1-100).
        output_filename (str, optional): Custom output filename. If None,
                                         auto-generates based on source name.

    Returns:
        str: Path to the exported file.
    """
    # Open the source image
    img = Image.open(image_path).convert("RGB")

    # Generate output filename if not specified
    if output_filename is None:
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        ext = "jpg" if fmt.lower() in ("jpeg", "jpg") else fmt.lower()
        output_filename = "{}_export.{}".format(base_name, ext)

    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Save in the specified format with appropriate settings
    fmt_upper = fmt.upper()
    if fmt_upper in ("JPEG", "JPG"):
        # JPEG: lossy compression with optimization
        img.save(output_path, "JPEG", quality=quality, optimize=True)
    elif fmt_upper == "WEBP":
        # WebP: modern format with quality control
        img.save(output_path, "WEBP", quality=quality)
    else:
        # PNG: lossless compression with optimization
        img.save(output_path, "PNG", optimize=True)

    # Display file size information
    file_size = os.path.getsize(output_path)
    size_str = "{:.1f} KB".format(file_size / 1024)
    if file_size > 1024 * 1024:
        size_str = "{:.1f} MB".format(file_size / (1024 * 1024))

    print("  Exported: {} ({})".format(output_path, size_str))
    return output_path


def export_for_platform(image_path, platform_choice):
    """
    Export an image optimized for a specific ad platform.

    Automatically resizes the image to the platform's recommended dimensions
    and saves it in the platform's preferred format.

    Args:
        image_path (str): Path to the source image file.
        platform_choice (str): Key from PLATFORM_PRESETS dict.

    Returns:
        str: Path to the exported file, or None if export failed.
    """
    # Get platform preset configuration
    preset = PLATFORM_PRESETS.get(platform_choice)
    if not preset:
        print("  [ERROR] Unknown platform preset: {}".format(platform_choice))
        return None

    platform_name = preset["name"]
    print("\n  Exporting for: {}".format(platform_name))

    # Open the source image
    img = Image.open(image_path).convert("RGB")

    # Resize if platform specifies dimensions
    if preset["width"] and preset["height"]:
        img = img.resize(
            (preset["width"], preset["height"]),
            Image.Resampling.LANCZOS
        )
        print("  Resized to: {}x{}".format(preset["width"], preset["height"]))

    # Determine output format and filename
    fmt = preset.get("format") or "png"
    ext = "jpg" if fmt in ("jpeg", "jpg") else fmt
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    safe_platform = platform_name.lower().replace(" ", "_").replace("/", "_")
    output_filename = "{}_{}.{}".format(base_name, safe_platform, ext)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Save with format-specific settings
    if fmt in ("jpeg", "jpg"):
        img.save(output_path, "JPEG", quality=85, optimize=True)
    elif fmt == "webp":
        img.save(output_path, "WEBP", quality=90)
    else:
        img.save(output_path, "PNG", optimize=True)

    # Display file size
    file_size = os.path.getsize(output_path)
    size_str = "{:.1f} KB".format(file_size / 1024)
    print("  Saved: {} ({})".format(output_path, size_str))

    return output_path


def list_generated_images():
    """
    List all generated images in the output directory.

    Scans the output directory for image files and returns their
    details sorted by modification time (newest first).

    Returns:
        list: List of dicts with keys "index", "filename", "path", "size".
              Returns empty list if output directory doesn't exist.
    """
    # Check if output directory exists
    if not os.path.exists(OUTPUT_DIR):
        return []

    # Supported image extensions
    image_extensions = (".png", ".jpg", ".jpeg", ".webp")

    # Collect all image files
    images = []
    for filename in os.listdir(OUTPUT_DIR):
        if filename.lower().endswith(image_extensions):
            filepath = os.path.join(OUTPUT_DIR, filename)
            file_size = os.path.getsize(filepath)
            images.append({
                "filename": filename,
                "path": filepath,
                "size": file_size,
            })

    # Sort by modification time (newest first)
    images.sort(key=lambda x: os.path.getmtime(x["path"]), reverse=True)

    # Add index numbers for display
    for i, img in enumerate(images):
        img["index"] = i + 1

    return images
