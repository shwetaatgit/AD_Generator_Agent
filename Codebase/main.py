"""
main.py - Ad Creator: CLI Entry Point

Advertisement Creator Using AI Image Generation
================================================

This is the main entry point for the Ad Creator application. It provides
an interactive command-line interface (CLI) for generating advertisement
images using AI image generation models.

Two AI Models Used (from Two Different Providers):
    1. Stable Diffusion XL (Stability AI) via Hugging Face Inference API
       - High-quality, versatile image generation
       - Requires free HF token from huggingface.co
    2. FLUX (Black Forest Labs) via Pollinations.ai
       - Excellent prompt adherence, photorealistic
       - Completely free, no API key required

Usage:
    1. Edit .env file and paste your Hugging Face token
    2. python main.py

Features:
    - Generate ad images with multiple AI models
    - Compare outputs from different models side-by-side
    - Post-process: text overlay, logo, brightness/contrast
    - Export in PNG/JPEG/WebP for various ad platforms
    - Browse and manage generated image gallery
"""

import os
import sys

# Load environment variables from .env file (contains HF token)
# python-dotenv reads .env file and sets environment variables automatically
from dotenv import load_dotenv
load_dotenv()

# Import project modules
from config import (
    MODELS, AD_FORMATS, STYLES, PRODUCT_CATEGORIES,
    EXPORT_FORMATS, PLATFORM_PRESETS, OUTPUT_DIR,
    HF_API_TOKEN_ENV,
)
from prompt_builder import build_prompt, preview_prompt
from image_generator import generate_images, compare_models
from post_processor import add_text_overlay, add_logo, adjust_image
from exporter import export_image, export_for_platform, list_generated_images


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_screen():
    """Clear the terminal screen for cleaner UI."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Print the application header/banner."""
    print("=" * 60)
    print("  AD CREATOR - AI Image Generation")
    print("  Using FLUX & Stable Diffusion XL Turbo")
    print("=" * 60)


def print_menu(title, options, show_back=True):
    """
    Display a numbered menu and return the user's choice.

    Args:
        title (str): Menu title to display.
        options (dict): Dict of {key: {name, ...}} or {key: {name, description}}.
        show_back (bool): Whether to show a "Back" option.

    Returns:
        str: The selected key, or None if user chose to go back.
    """
    print("\n--- {} ---".format(title))
    for key, val in options.items():
        name = val.get("name", val) if isinstance(val, dict) else val
        desc = val.get("description", "") if isinstance(val, dict) else ""
        if desc:
            print("  [{}] {} - {}".format(key, name, desc))
        else:
            print("  [{}] {}".format(key, name))

    if show_back:
        print("  [0] Back")

    choice = input("\n  Select option: ").strip()
    if choice == "0" and show_back:
        return None
    return choice


def get_input(prompt_text, default=None, required=False):
    """
    Get user input with optional default value.

    Args:
        prompt_text (str): Text to display as the input prompt.
        default: Default value if user presses Enter without typing.
        required (bool): If True, keeps asking until input is provided.

    Returns:
        str: The user's input or the default value.
    """
    if default is not None:
        display = "{} [{}]: ".format(prompt_text, default)
    else:
        display = "{}: ".format(prompt_text)

    while True:
        value = input(display).strip()
        if not value and default is not None:
            return str(default)
        if not value and required:
            print("  This field is required. Please enter a value.")
            continue
        if value:
            return value
        return ""


def get_int_input(prompt_text, default=None, min_val=None, max_val=None):
    """
    Get an integer input from the user with validation.

    Args:
        prompt_text (str): Text to display as the input prompt.
        default (int): Default value if user presses Enter.
        min_val (int): Minimum allowed value.
        max_val (int): Maximum allowed value.

    Returns:
        int: The validated integer input.
    """
    while True:
        value = get_input(prompt_text, default)
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                print("  Value must be at least {}".format(min_val))
                continue
            if max_val is not None and num > max_val:
                print("  Value must be at most {}".format(max_val))
                continue
            return num
        except ValueError:
            print("  Please enter a valid number.")


def get_float_input(prompt_text, default=None, min_val=None, max_val=None):
    """
    Get a float input from the user with validation.

    Args:
        prompt_text (str): Text to display as the input prompt.
        default (float): Default value if user presses Enter.
        min_val (float): Minimum allowed value.
        max_val (float): Maximum allowed value.

    Returns:
        float: The validated float input.
    """
    while True:
        value = get_input(prompt_text, default)
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                print("  Value must be at least {}".format(min_val))
                continue
            if max_val is not None and num > max_val:
                print("  Value must be at most {}".format(max_val))
                continue
            return num
        except ValueError:
            print("  Please enter a valid number.")


# =============================================================================
# FEATURE: CREATE NEW ADVERTISEMENT
# =============================================================================

def create_advertisement():
    """
    Interactive workflow to create a new advertisement image.

    Guides the user through:
    1. Entering product/brand details
    2. Selecting ad format, style, and category
    3. Choosing the AI model
    4. Previewing the prompt
    5. Generating images
    6. Optional post-processing
    """
    print("\n" + "=" * 60)
    print("  CREATE NEW ADVERTISEMENT")
    print("=" * 60)

    # Step 1: Product Details
    print("\n--- Step 1: Product Details ---")
    product_name = get_input("  Product/Brand Name", required=True)
    product_description = get_input("  Description (what is being advertised)")
    custom_keywords = get_input("  Custom Keywords (e.g., summer sale, 50% off)")
    brand_colors = get_input("  Brand Colors (e.g., red and white)")

    # Step 2: Ad Configuration
    print("\n--- Step 2: Ad Format ---")
    format_choice = print_menu("Ad Format", AD_FORMATS, show_back=False)
    if format_choice not in AD_FORMATS:
        format_choice = "1"  # Default to Instagram Post

    # Handle custom size
    format_data = AD_FORMATS[format_choice]
    if format_data["category"] == "custom":
        custom_w = get_int_input("  Width (pixels)", 1024, 64, 2048)
        custom_h = get_int_input("  Height (pixels)", 1024, 64, 2048)
        AD_FORMATS[format_choice]["width"] = custom_w
        AD_FORMATS[format_choice]["height"] = custom_h

    print("\n--- Step 2b: Visual Style ---")
    style_choice = print_menu("Visual Style", STYLES, show_back=False)
    if style_choice not in STYLES:
        style_choice = "6"  # Default to Minimal

    print("\n--- Step 2c: Product Category ---")
    category_choice = print_menu("Product Category", PRODUCT_CATEGORIES, show_back=False)
    if category_choice not in PRODUCT_CATEGORIES:
        category_choice = "10"  # Default to General

    # Step 3: Model Selection
    print("\n--- Step 3: AI Model Selection ---")
    model_choice = print_menu("AI Model", MODELS, show_back=False)
    if model_choice not in MODELS:
        model_choice = "1"  # Default to FLUX

    # Step 4: Generation Settings
    num_images = get_int_input("\n  Number of images to generate (1-4)", 2, 1, 4)

    seed_input = get_input("  Seed for reproducibility (Enter for random)")
    seed = int(seed_input) if seed_input else None

    # Step 5: Preview Prompt
    prompt_data = build_prompt(
        product_name=product_name,
        product_description=product_description,
        style_key=style_choice,
        category_key=category_choice,
        format_key=format_choice,
        custom_keywords=custom_keywords,
        brand_colors=brand_colors,
    )

    print("\n--- Prompt Preview ---")
    print("  " + prompt_data["prompt"][:200] + "...")
    print("\n  Format: {} ({}x{})".format(
        AD_FORMATS[format_choice]["name"],
        prompt_data["width"], prompt_data["height"]
    ))
    print("  Model: {}".format(MODELS[model_choice]["name"]))

    # Confirm generation
    confirm = get_input("\n  Generate images? (y/n)", "y")
    if confirm.lower() != "y":
        print("  Generation cancelled.")
        return

    # Step 6: Generate Images
    results = generate_images(
        prompt=prompt_data["prompt"],
        negative_prompt=prompt_data["negative_prompt"],
        model_choice=model_choice,
        width=prompt_data["width"],
        height=prompt_data["height"],
        num_images=num_images,
        seed=seed,
    )

    if not results:
        print("\n  [ERROR] No images were generated. Please try again.")
        return

    # Display results summary
    print("\n--- Generation Complete ---")
    print("  Generated {} image(s):".format(len(results)))
    for i, img in enumerate(results):
        print("  [{}] {} ({}x{}, {})".format(
            i + 1, img["filename"], img["width"], img["height"], img["model"]
        ))

    # Offer post-processing
    post_process_menu(results)


# =============================================================================
# FEATURE: MULTI-MODEL COMPARISON
# =============================================================================

def model_comparison():
    """
    Generate the same advertisement with both FLUX and SDXL Turbo models.

    This demonstrates the two-LLM requirement by producing comparable
    outputs from different model architectures using identical prompts.
    """
    print("\n" + "=" * 60)
    print("  MULTI-MODEL COMPARISON (FLUX vs SDXL Turbo)")
    print("=" * 60)

    # Get product details
    print("\n--- Product Details ---")
    product_name = get_input("  Product/Brand Name", required=True)
    product_description = get_input("  Description")
    custom_keywords = get_input("  Custom Keywords")

    # Quick style selection
    print("\n--- Quick Style ---")
    style_choice = print_menu("Visual Style", STYLES, show_back=False)
    if style_choice not in STYLES:
        style_choice = "3"

    category_choice = "10"  # General
    print("\n  Using square format (1024x1024) for fair comparison.")

    # Build prompt
    prompt_data = build_prompt(
        product_name=product_name,
        product_description=product_description,
        style_key=style_choice,
        category_key=category_choice,
        format_key="1",  # Instagram Post (square)
        custom_keywords=custom_keywords,
    )

    # Generate with both models
    results = compare_models(
        prompt=prompt_data["prompt"],
        width=1024,
        height=1024,
        seed=42,
    )

    if results:
        print("\n--- Comparison Results ---")
        for img in results:
            print("  - {} [{}]".format(img["filename"], img["model"]))
        print("\n  Images saved to: {}".format(OUTPUT_DIR))
        print("  Compare the two outputs to see how different models")
        print("  interpret the same advertisement prompt.")


# =============================================================================
# FEATURE: POST-PROCESSING
# =============================================================================

def post_process_menu(images=None):
    """
    Interactive post-processing menu for generated or existing images.

    Allows users to apply text overlays, logos, and image adjustments
    to their generated advertisement images.

    Args:
        images (list, optional): List of image dicts from generation.
                                 If None, loads from gallery.
    """
    # If no images provided, load from gallery
    if images is None:
        images_list = list_generated_images()
        if not images_list:
            print("\n  No images found in gallery. Generate some first!")
            return
        print("\n--- Select Image to Edit ---")
        for img in images_list:
            print("  [{}] {}".format(img["index"], img["filename"]))
        idx = get_int_input("  Select image number", 1, 1, len(images_list))
        selected = images_list[idx - 1]
        image_path = selected["path"]
    else:
        # Use images from recent generation
        if len(images) == 1:
            image_path = images[0]["path"]
        else:
            print("\n--- Select Image to Edit ---")
            for i, img in enumerate(images):
                print("  [{}] {}".format(i + 1, img["filename"]))
            print("  [0] Skip post-processing")
            idx = get_int_input("  Select image", 0, 0, len(images))
            if idx == 0:
                return
            image_path = images[idx - 1]["path"]

    # Post-processing loop
    while True:
        print("\n--- Post-Processing: {} ---".format(os.path.basename(image_path)))
        print("  [1] Add Text Overlay (headline, tagline, CTA)")
        print("  [2] Add Logo")
        print("  [3] Adjust Image (brightness, contrast, saturation)")
        print("  [4] Export / Download")
        print("  [0] Done")

        choice = get_input("  Select option", "0")

        if choice == "1":
            # Text Overlay
            headline = get_input("  Headline text")
            tagline = get_input("  Tagline text")
            cta_text = get_input("  CTA button text (e.g., Shop Now)")
            color = get_input("  Text color (hex)", "#FFFFFF")
            position = get_input("  Position (top/center/bottom)", "bottom")
            opacity = get_float_input("  Overlay opacity (0.0-1.0)", 0.5, 0.0, 1.0)

            result = add_text_overlay(
                image_path, headline, tagline, cta_text,
                color, position, opacity
            )
            result.save(image_path)
            print("  Text overlay applied and saved!")

        elif choice == "2":
            # Logo
            logo_path = get_input("  Logo file path", required=True)
            if not os.path.exists(logo_path):
                print("  [ERROR] File not found: {}".format(logo_path))
                continue
            position = get_input("  Position (top-left/top-right/bottom-left/bottom-right/center)", "top-right")
            scale = get_float_input("  Logo scale (0.05-0.4)", 0.15, 0.05, 0.4)

            result = add_logo(image_path, logo_path, position, scale)
            result.save(image_path)
            print("  Logo added and saved!")

        elif choice == "3":
            # Image Adjustments
            brightness = get_float_input("  Brightness (0.5-2.0, 1.0=normal)", 1.0, 0.5, 2.0)
            contrast = get_float_input("  Contrast (0.5-2.0, 1.0=normal)", 1.0, 0.5, 2.0)
            saturation = get_float_input("  Saturation (0.0-2.0, 1.0=normal)", 1.0, 0.0, 2.0)
            blur = get_float_input("  Blur radius (0-10, 0=none)", 0, 0, 10)

            result = adjust_image(image_path, brightness, contrast, saturation, blur)
            result.save(image_path)
            print("  Adjustments applied and saved!")

        elif choice == "4":
            # Export
            export_menu(image_path)

        else:
            break


# =============================================================================
# FEATURE: EXPORT
# =============================================================================

def export_menu(image_path=None):
    """
    Export an image in various formats and platform-optimized sizes.

    Args:
        image_path (str, optional): Path to image. If None, prompts selection.
    """
    # Select image if not provided
    if image_path is None:
        images_list = list_generated_images()
        if not images_list:
            print("\n  No images found. Generate some first!")
            return
        print("\n--- Select Image to Export ---")
        for img in images_list:
            size_kb = img["size"] / 1024
            print("  [{}] {} ({:.1f} KB)".format(img["index"], img["filename"], size_kb))
        idx = get_int_input("  Select image number", 1, 1, len(images_list))
        image_path = images_list[idx - 1]["path"]

    print("\n--- Export Options ---")
    print("  [1] Export in specific format (PNG/JPEG/WebP)")
    print("  [2] Export for ad platform (auto-resize)")
    print("  [0] Back")

    choice = get_input("  Select option", "0")

    if choice == "1":
        # Format export
        fmt_choice = print_menu("Export Format", EXPORT_FORMATS, show_back=False)
        if fmt_choice not in EXPORT_FORMATS:
            fmt_choice = "1"
        fmt_data = EXPORT_FORMATS[fmt_choice]
        quality = get_int_input("  Quality (1-100)", fmt_data["quality"], 1, 100)
        export_image(image_path, fmt_data["extension"], quality)

    elif choice == "2":
        # Platform export
        platform_choice = print_menu("Platform Preset", PLATFORM_PRESETS, show_back=False)
        if platform_choice in PLATFORM_PRESETS:
            export_for_platform(image_path, platform_choice)


# =============================================================================
# FEATURE: GALLERY
# =============================================================================

def view_gallery():
    """
    Display all generated images in the output directory.

    Shows image filenames with sizes and provides options to
    post-process, export, or delete images.
    """
    print("\n" + "=" * 60)
    print("  IMAGE GALLERY")
    print("=" * 60)

    images = list_generated_images()
    if not images:
        print("\n  No images found in '{}'. Generate some first!".format(OUTPUT_DIR))
        return

    # Display image list
    print("\n  Found {} image(s):\n".format(len(images)))
    for img in images:
        size_kb = img["size"] / 1024
        if size_kb > 1024:
            size_str = "{:.1f} MB".format(size_kb / 1024)
        else:
            size_str = "{:.1f} KB".format(size_kb)
        print("  [{}] {} ({})".format(img["index"], img["filename"], size_str))

    # Gallery actions
    print("\n--- Actions ---")
    print("  [E] Export an image")
    print("  [P] Post-process an image")
    print("  [D] Delete an image")
    print("  [0] Back")

    choice = get_input("  Select action", "0").upper()

    if choice == "E":
        idx = get_int_input("  Image number to export", 1, 1, len(images))
        export_menu(images[idx - 1]["path"])

    elif choice == "P":
        idx = get_int_input("  Image number to edit", 1, 1, len(images))
        post_process_menu([{"path": images[idx - 1]["path"],
                            "filename": images[idx - 1]["filename"]}])

    elif choice == "D":
        idx = get_int_input("  Image number to delete", 1, 1, len(images))
        confirm = get_input("  Delete {}? (y/n)".format(images[idx - 1]["filename"]), "n")
        if confirm.lower() == "y":
            os.remove(images[idx - 1]["path"])
            print("  Deleted: {}".format(images[idx - 1]["filename"]))


# =============================================================================
# MAIN MENU AND ENTRY POINT
# =============================================================================

def main_menu():
    """
    Display the main application menu and handle user navigation.

    This is the primary loop that runs the CLI application, presenting
    the user with options to create ads, compare models, manage gallery,
    and export images.
    """
    print_header()
    print("\n  Models Available:")
    print("    1. Stable Diffusion XL (Hugging Face) - High quality, versatile")
    print("    2. FLUX (Pollinations.ai) - Excellent prompt adherence, free")
    print("    3. SDXL Turbo (Pollinations.ai) - Fast generation, free")

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Check for Hugging Face API token
    hf_token = os.environ.get(HF_API_TOKEN_ENV)
    if hf_token:
        print("\n  Hugging Face token: Configured")
    else:
        print("\n  Hugging Face token: NOT SET")
        print("  To use SDXL (high quality), get a free token at https://huggingface.co/settings/tokens")
        key_input = input("  Enter HF token (or press Enter to skip): ").strip()
        if key_input:
            os.environ[HF_API_TOKEN_ENV] = key_input
            print("  Token set for this session!")
        else:
            print("  Skipped. You can still use FLUX and SDXL Turbo (Pollinations) without a token.")

    while True:
        print("\n" + "-" * 40)
        print("  MAIN MENU")
        print("-" * 40)
        print("  [1] Create New Advertisement")
        print("  [2] Multi-Model Comparison (FLUX vs SDXL)")
        print("  [3] Post-Process Existing Image")
        print("  [4] Export Image")
        print("  [5] View Gallery")
        print("  [6] Exit")

        choice = get_input("\n  Select option")

        if choice == "1":
            create_advertisement()
        elif choice == "2":
            model_comparison()
        elif choice == "3":
            post_process_menu()
        elif choice == "4":
            export_menu()
        elif choice == "5":
            view_gallery()
        elif choice == "6":
            print("\n  Thank you for using Ad Creator!")
            print("  Generated images are saved in: {}\n".format(OUTPUT_DIR))
            sys.exit(0)
        else:
            print("  Invalid option. Please try again.")


# Entry point - run the main menu when script is executed directly
if __name__ == "__main__":
    main_menu()
