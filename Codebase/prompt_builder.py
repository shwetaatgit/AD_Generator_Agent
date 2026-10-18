"""
prompt_builder.py - Intelligent Prompt Engineering for Ad Generation

This module constructs optimized prompts for AI image generation models
by combining product details, visual styles, ad format specifications,
and quality-enhancing tokens. The prompt builder ensures that generated
images look like professional advertisements rather than plain photos.

Key Features:
    - Combines multiple signal sources (product, style, category, format)
    - Adds advertisement-specific design tokens (layout, typography areas)
    - Adjusts composition hints based on aspect ratio
    - Provides negative prompts to avoid common generation artifacts
"""

from config import STYLES, PRODUCT_CATEGORIES, AD_FORMATS


# =============================================================================
# PROMPT ENHANCEMENT TOKENS
# =============================================================================

# Quality tokens appended to every prompt to ensure high-resolution output
QUALITY_ENHANCERS = (
    "high resolution, studio quality, sharp focus, 8k, "
    "professional graphic design, print ready"
)

# Negative prompt tokens to avoid common issues in generated images
NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, deformed, ugly, "
    "watermark, bad anatomy, disfigured, poorly drawn, "
    "extra limbs, grainy, amateur, stock photo, plain photo"
)

# Core advertisement design tokens that make the output look like an ad
# rather than a regular photo - includes layout, typography, and branding elements
AD_LAYOUT_TOKENS = (
    "commercial advertisement poster design, "
    "graphic design layout with text space, "
    "marketing banner with headline area and call-to-action button, "
    "promotional flyer design, advertising campaign visual, "
    "bold typography area, branded design composition"
)

# Format-specific hints based on ad category
FORMAT_HINTS = {
    "social": "social media ad post design, digital marketing creative",
    "story": "vertical story ad design, full-screen mobile advertisement",
    "banner": "web banner ad design, digital display advertisement",
    "display": "display advertisement design, billboard style layout",
    "custom": "professional advertisement design, marketing visual",
}


def build_prompt(product_name, product_description, style_key, category_key,
                 format_key, custom_keywords="", brand_colors=""):
    """
    Build an optimized prompt for advertisement image generation.

    This function combines multiple inputs to create a detailed prompt that
    guides the AI model to generate advertisement-style images. The prompt
    includes product information, visual style tokens, category-specific
    tokens, format hints, and quality enhancers.

    Args:
        product_name (str): Name of the product or brand being advertised.
        product_description (str): Brief description of the product/service.
        style_key (str): Key from STYLES dict (e.g., "1" for Emotional).
        category_key (str): Key from PRODUCT_CATEGORIES dict.
        format_key (str): Key from AD_FORMATS dict.
        custom_keywords (str): Optional custom keywords from the user.
        brand_colors (str): Optional brand color preferences.

    Returns:
        dict: Contains 'prompt' (str), 'negative_prompt' (str),
              'width' (int), and 'height' (int).
    """
    # Retrieve style, category, and format data from configuration
    style_data = STYLES.get(style_key, STYLES["6"])  # Default to Minimal
    category_data = PRODUCT_CATEGORIES.get(category_key, PRODUCT_CATEGORIES["10"])
    format_data = AD_FORMATS.get(format_key, AD_FORMATS["1"])

    # Determine the format category for format-specific hints
    format_category = format_data.get("category", "social")
    format_hint = FORMAT_HINTS.get(format_category, FORMAT_HINTS["custom"])

    # Build the prompt by combining all components in order of importance
    prompt_parts = [
        # Primary: What is being advertised
        "Professional advertisement poster for {}".format(product_name),
        # Advertisement design elements
        AD_LAYOUT_TOKENS,
        # Product description from user
        product_description,
        # Format-specific design hints
        format_hint,
        # Visual style tokens
        style_data["tokens"],
        # Product category tokens
        category_data["tokens"],
        # Quality enhancement tokens
        QUALITY_ENHANCERS,
    ]

    # Insert custom keywords if provided (after product description)
    if custom_keywords:
        prompt_parts.insert(3, custom_keywords)

    # Add brand color preferences if specified
    if brand_colors:
        prompt_parts.append("color scheme: {}".format(brand_colors))

    # Add composition hints based on the aspect ratio of the ad format
    width = format_data.get("width") or 1024
    height = format_data.get("height") or 1024

    aspect = width / height
    if aspect > 1.2:
        # Landscape orientation (e.g., Facebook post, web banner)
        prompt_parts.append("landscape orientation, wide banner composition")
    elif aspect < 0.8:
        # Portrait orientation (e.g., Instagram story)
        prompt_parts.append("portrait orientation, vertical poster composition")
    else:
        # Square or near-square (e.g., Instagram post)
        prompt_parts.append("square composition, centered poster layout")

    # Join all non-empty parts with commas
    prompt = ", ".join(part for part in prompt_parts if part)

    return {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "width": width,
        "height": height,
    }


def preview_prompt(product_name, product_description, style_key, category_key,
                   format_key, custom_keywords="", brand_colors=""):
    """
    Generate and display a preview of the prompt that will be sent to the model.

    This allows users to review and refine their inputs before generating images.
    Useful for understanding how different settings affect the final prompt.

    Args:
        Same as build_prompt().

    Returns:
        str: The constructed prompt string for display.
    """
    result = build_prompt(
        product_name, product_description, style_key, category_key,
        format_key, custom_keywords, brand_colors
    )
    return result["prompt"]
