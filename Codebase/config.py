"""
config.py - Configuration and Constants for Ad Creator

This module defines all configuration constants, model definitions,
ad templates, style presets, and product categories used throughout
the application. Centralizing configuration here makes it easy to
modify parameters without changing core logic.

Models Used (Two Distinct LLMs from Two Different Providers):
    1. Stable Diffusion XL (Stability AI) via Hugging Face Inference API
       - High-quality latent diffusion model for text-to-image generation
       - Accessed via HF Inference API (requires free HF token)
    2. Stable Diffusion XL Turbo (Stability AI) via Pollinations.ai
       - Fast variant with adversarial distillation
       - Free API, no key required
"""

import os

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

# Directory where generated images will be saved
OUTPUT_DIR = "./outputs"

# Maximum number of images that can be generated per request
MAX_IMAGES_PER_REQUEST = 4

# Default image dimensions (width x height in pixels)
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024

# =============================================================================
# HUGGING FACE INFERENCE API CONFIGURATION (Model 1)
# =============================================================================
# Hugging Face provides an Inference API for running models in the cloud
# Sign up at https://huggingface.co and create a token with Inference access
# Set token via environment variable: export HUGGINGFACE_API_TOKEN=hf_xxx

HF_API_TOKEN_ENV = "HUGGINGFACE_API_TOKEN"

# Request timeout in seconds
REQUEST_TIMEOUT = 120

# =============================================================================
# POLLINATIONS.AI API CONFIGURATION (Model 2)
# =============================================================================
# Pollinations.ai provides free access without any API key

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

# =============================================================================
# MODEL DEFINITIONS
# =============================================================================
# Two distinct models from two different providers:
#
# Model 1: Stable Diffusion XL (Stability AI) via Hugging Face
#   - Architecture: Latent diffusion model with 3.5B parameter UNet
#   - Strengths: High quality, versatile, excellent for advertisements
#   - Provider: Hugging Face Inference API (free tier with monthly credits)
#   - Justification: SDXL is the industry standard open-source model for
#     high-quality image generation. It produces detailed, sharp images
#     with strong composition suitable for professional ads.
#
# Model 2: FLUX (Black Forest Labs) via Pollinations.ai
#   - Architecture: Flow-matching based diffusion model
#   - Strengths: Excellent prompt adherence, fast via Pollinations
#   - Provider: Pollinations.ai (completely free, no API key)
#   - Justification: FLUX uses a fundamentally different architecture
#     (flow-matching vs latent diffusion), producing distinctly different
#     artistic interpretations with strong prompt following ability.

MODELS = {
    "1": {
        "key": "sdxl-hf",
        "name": "Stable Diffusion XL (Hugging Face)",
        "api_model": "stabilityai/stable-diffusion-xl-base-1.0",
        "provider": "huggingface",
        "description": "High quality, versatile (needs HF token)",
    },
    "2": {
        "key": "flux-pollinations",
        "name": "FLUX (Pollinations.ai)",
        "api_model": "flux",
        "provider": "pollinations",
        "description": "Excellent prompt adherence (FREE, no key)",
    },
    "3": {
        "key": "sdxl-turbo",
        "name": "SDXL Turbo (Pollinations.ai)",
        "api_model": "turbo",
        "provider": "pollinations",
        "description": "Fast generation (FREE, no key)",
    },
}

# =============================================================================
# AD FORMAT DEFINITIONS
# =============================================================================
# Standard advertisement dimensions for popular platforms

AD_FORMATS = {
    "1": {
        "name": "Instagram Post",
        "width": 1080,
        "height": 1080,
        "category": "social",
    },
    "2": {
        "name": "Instagram Story",
        "width": 1080,
        "height": 1920,
        "category": "story",
    },
    "3": {
        "name": "Facebook Post",
        "width": 1200,
        "height": 628,
        "category": "social",
    },
    "4": {
        "name": "Twitter/X Post",
        "width": 1600,
        "height": 900,
        "category": "social",
    },
    "5": {
        "name": "LinkedIn Post",
        "width": 1200,
        "height": 627,
        "category": "social",
    },
    "6": {
        "name": "YouTube Thumbnail",
        "width": 1280,
        "height": 720,
        "category": "social",
    },
    "7": {
        "name": "Web Banner (728x90)",
        "width": 728,
        "height": 90,
        "category": "banner",
    },
    "8": {
        "name": "Billboard (970x250)",
        "width": 970,
        "height": 250,
        "category": "display",
    },
    "9": {
        "name": "Custom Size",
        "width": None,
        "height": None,
        "category": "custom",
    },
}

# =============================================================================
# VISUAL STYLE PRESETS
# =============================================================================
# Each style adds specific tokens to the prompt to guide the model's output

STYLES = {
    "1": {
        "name": "Emotional",
        "description": "Heartwarming, human connection, storytelling",
        "tokens": "emotional storytelling ad, warm lighting, cinematic composition, inviting atmosphere, lifestyle advertisement",
    },
    "2": {
        "name": "Informative",
        "description": "Clean, professional, data-driven",
        "tokens": "clean ad layout, professional design, modern typography, corporate branding, structured grid layout",
    },
    "3": {
        "name": "Call to Action",
        "description": "Bold, urgent, compelling",
        "tokens": "bold promotional design, eye-catching sale banner, dynamic composition, vibrant colors, high contrast, urgent offer design",
    },
    "4": {
        "name": "Luxury",
        "description": "Elegant, premium, sophisticated",
        "tokens": "luxury brand advertisement, elegant premium design, dark background with gold accents, sophisticated high-end marketing",
    },
    "5": {
        "name": "Playful",
        "description": "Fun, vibrant, energetic",
        "tokens": "fun vibrant ad design, colorful marketing poster, energetic youthful branding, bright pop art style advertisement",
    },
    "6": {
        "name": "Minimal",
        "description": "Minimalist, clean, simple",
        "tokens": "minimalist ad design, clean white space layout, modern sleek branding, simple elegant advertisement poster",
    },
    "7": {
        "name": "Retro / Vintage",
        "description": "Nostalgic, classic, throwback",
        "tokens": "retro vintage advertisement design, nostalgic classic poster, muted tones, throwback marketing style",
    },
    "8": {
        "name": "Tech / Futuristic",
        "description": "Modern, innovative, cutting-edge",
        "tokens": "futuristic tech advertisement, neon glow design, digital innovative branding, sci-fi aesthetics poster",
    },
}

# =============================================================================
# PRODUCT CATEGORY PRESETS
# =============================================================================

PRODUCT_CATEGORIES = {
    "1": {
        "name": "Food & Beverage",
        "tokens": "appetizing food advertisement, restaurant promotional design, delicious dish showcase, menu style layout",
    },
    "2": {
        "name": "Fashion & Apparel",
        "tokens": "fashion advertisement, stylish trendy editorial, clothing brand design, apparel marketing",
    },
    "3": {
        "name": "Technology",
        "tokens": "tech gadget advertisement, sleek device design, innovation product shot, technology marketing",
    },
    "4": {
        "name": "Health & Fitness",
        "tokens": "health fitness advertisement, active lifestyle design, wellness vitality marketing, gym promotional",
    },
    "5": {
        "name": "Travel & Tourism",
        "tokens": "travel tourism advertisement, scenic destination design, adventure wanderlust marketing, vacation promotional",
    },
    "6": {
        "name": "Beauty & Cosmetics",
        "tokens": "beauty cosmetics advertisement, glowing skin design, elegant makeup marketing, skincare promotional",
    },
    "7": {
        "name": "Automotive",
        "tokens": "automotive car advertisement, speed design engineering, vehicle marketing, automobile promotional",
    },
    "8": {
        "name": "Real Estate",
        "tokens": "real estate advertisement, property architecture design, home interior marketing, housing promotional",
    },
    "9": {
        "name": "Education",
        "tokens": "education advertisement, learning knowledge design, academic bright future marketing, institution promotional",
    },
    "10": {
        "name": "General / Other",
        "tokens": "commercial advertisement, professional marketing design, brand promotional poster",
    },
}

# =============================================================================
# EXPORT FORMAT PRESETS
# =============================================================================

EXPORT_FORMATS = {
    "1": {"name": "PNG (Lossless)", "extension": "png", "quality": 100},
    "2": {"name": "JPEG (Web optimized)", "extension": "jpg", "quality": 85},
    "3": {"name": "WebP (Modern format)", "extension": "webp", "quality": 90},
}

# =============================================================================
# PLATFORM EXPORT PRESETS
# =============================================================================

PLATFORM_PRESETS = {
    "1": {"name": "Instagram Post", "width": 1080, "height": 1080, "format": "jpg"},
    "2": {"name": "Instagram Story", "width": 1080, "height": 1920, "format": "jpg"},
    "3": {"name": "Facebook Post", "width": 1200, "height": 628, "format": "jpg"},
    "4": {"name": "Twitter/X Post", "width": 1600, "height": 900, "format": "png"},
    "5": {"name": "LinkedIn Post", "width": 1200, "height": 627, "format": "png"},
    "6": {"name": "YouTube Thumbnail", "width": 1280, "height": 720, "format": "jpg"},
    "7": {"name": "Original Size", "width": None, "height": None, "format": None},
}
