"""
image_generator.py - Multi-Model Image Generation Engine

This module handles image generation using two distinct AI models from
two different providers:

    Model 1: Stable Diffusion XL (Stability AI) via Hugging Face Inference API
        - Architecture: Latent diffusion model with 3.5B parameter UNet
        - Strengths: High quality, versatile, detailed output
        - API: Hugging Face Inference API (requires free HF token)

    Model 2: FLUX (Black Forest Labs) via Pollinations.ai
        - Architecture: Flow-matching based diffusion model
        - Strengths: Excellent prompt adherence, photorealistic
        - API: Pollinations.ai (completely free, no authentication)

Hugging Face Inference API:
    Uses the huggingface_hub InferenceClient for text-to-image generation.
    Token from env: HUGGINGFACE_API_TOKEN

Pollinations.ai API:
    GET https://image.pollinations.ai/prompt/{prompt}?width=W&height=H&model=M
    No authentication required.
"""

import os
import io
import uuid
import math
import requests
from datetime import datetime
from PIL import Image

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from config import (
    POLLINATIONS_BASE_URL,
    HF_API_TOKEN_ENV,
    OUTPUT_DIR,
    MAX_IMAGES_PER_REQUEST,
    REQUEST_TIMEOUT,
    MODELS,
)


def ensure_output_dir():
    """
    Create the output directory if it doesn't exist.
    Called before any image generation to ensure save location is available.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print("[INFO] Created output directory: {}".format(OUTPUT_DIR))


def get_hf_token():
    """
    Retrieve the Hugging Face API token from environment variable.

    The token can be set via:
        export HUGGINGFACE_API_TOKEN=hf_your_token_here

    Get a free token at https://huggingface.co/settings/tokens

    Returns:
        str or None: The API token, or None if not configured.
    """
    return os.environ.get(HF_API_TOKEN_ENV)


def clamp_dimensions(width, height, max_pixels=1048576):
    """
    Clamp image dimensions to stay within model limits while preserving aspect ratio.

    Most image generation models have a maximum pixel count they can handle.
    This function scales down dimensions if they exceed the limit, while
    maintaining the original aspect ratio. Dimensions are also aligned to
    multiples of 8 as required by diffusion models.

    Args:
        width (int): Desired image width in pixels.
        height (int): Desired image height in pixels.
        max_pixels (int): Maximum total pixel count (default: 1,048,576 = 1024x1024).

    Returns:
        tuple: (width, height) adjusted to fit within constraints.
    """
    # If within limits, just align to multiples of 8
    if width * height <= max_pixels:
        w = (width // 8) * 8
        h = (height // 8) * 8
        return max(w, 64), max(h, 64)

    # Scale down while preserving aspect ratio
    aspect = width / height
    h = int(math.sqrt(max_pixels / aspect))
    w = int(h * aspect)

    # Align to multiples of 8 (required by diffusion models)
    w = (w // 8) * 8
    h = (h // 8) * 8
    return max(w, 64), max(h, 64)


# =============================================================================
# HUGGING FACE INFERENCE API GENERATION (Stable Diffusion XL)
# =============================================================================

def generate_huggingface(prompt, model_id, width, height,
                         negative_prompt="", guidance_scale=7.5,
                         num_inference_steps=30, seed=None):
    """
    Generate a single image using Hugging Face Inference API.

    Uses the huggingface_hub InferenceClient to call the text-to-image
    endpoint for Stable Diffusion XL. The model runs on HF's servers
    so no local GPU is required.

    Args:
        prompt (str): The text prompt describing the desired image.
        model_id (str): HF model identifier (e.g., "stabilityai/stable-diffusion-xl-base-1.0").
        width (int): Desired image width in pixels.
        height (int): Desired image height in pixels.
        negative_prompt (str): Tokens describing what to avoid in generation.
        guidance_scale (float): How closely to follow the prompt (default: 7.5).
        num_inference_steps (int): Number of denoising steps (default: 30).
        seed (int, optional): Random seed for reproducibility.

    Returns:
        PIL.Image.Image: The generated image object.

    Raises:
        Exception: If API token is missing or request fails.
    """
    # Get HF token from environment
    token = get_hf_token()
    if not token:
        raise Exception(
            "Hugging Face API token not found. Set it with:\n"
            "  export HUGGINGFACE_API_TOKEN=hf_your_token_here\n"
            "  Get free token at: https://huggingface.co/settings/tokens"
        )

    # Import InferenceClient from huggingface_hub
    from huggingface_hub import InferenceClient

    # Create client with the user's token
    client = InferenceClient(token=token)

    # Build kwargs for the text_to_image call
    kwargs = {
        "prompt": prompt,
        "model": model_id,
        "width": width,
        "height": height,
        "guidance_scale": guidance_scale,
        "num_inference_steps": num_inference_steps,
    }

    # Add negative prompt if provided
    if negative_prompt:
        kwargs["negative_prompt"] = negative_prompt

    # Add seed if specified for reproducibility
    if seed is not None:
        kwargs["seed"] = seed

    print("  [API] Requesting image from Hugging Face ({})...".format(
        model_id.split("/")[-1]
    ))

    # Call the HF Inference API
    image = client.text_to_image(**kwargs)

    # Ensure we have a PIL Image object
    if isinstance(image, Image.Image):
        return image
    else:
        return Image.open(io.BytesIO(image))


# =============================================================================
# POLLINATIONS.AI GENERATION (FLUX / SDXL Turbo)
# =============================================================================

def generate_pollinations(prompt, model_key, width, height, seed=None):
    """
    Generate a single image using the Pollinations.ai API.

    Constructs the API URL with all parameters and sends a GET request.
    The API returns the generated image directly as binary data.
    No API key or authentication is required.

    Args:
        prompt (str): The text prompt describing the desired image.
        model_key (str): The Pollinations API model name (e.g., "flux", "turbo").
        width (int): Desired image width in pixels.
        height (int): Desired image height in pixels.
        seed (int, optional): Random seed for reproducibility.

    Returns:
        PIL.Image.Image: The generated image object.

    Raises:
        Exception: If the API request fails or returns invalid data.
    """
    # URL-encode the prompt to handle special characters
    encoded_prompt = quote(prompt)

    # Construct the API URL with parameters
    # nologo=true: removes the Pollinations watermark
    # enhance=true: applies quality enhancement to the output
    url = "{}/{}?width={}&height={}&model={}&nologo=true&enhance=true".format(
        POLLINATIONS_BASE_URL, encoded_prompt, width, height, model_key
    )

    # Add seed parameter if specified (for reproducible results)
    if seed is not None:
        url += "&seed={}".format(seed)

    print("  [API] Requesting image from Pollinations.ai ({})...".format(model_key))
    response = requests.get(url, timeout=REQUEST_TIMEOUT)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(
            "Pollinations API error ({}): {}".format(
                response.status_code, response.text[:200]
            )
        )

    # Parse the response content as an image
    image = Image.open(io.BytesIO(response.content))
    return image


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_images(prompt, negative_prompt="", model_choice="1",
                    width=1024, height=1024, num_images=1, seed=None):
    """
    Generate multiple advertisement images using the selected AI model.

    This is the main generation function that handles the full pipeline:
    1. Validates inputs and clamps dimensions
    2. Routes to the correct provider (Hugging Face or Pollinations.ai)
    3. Generates the requested number of images
    4. Saves each image to the output directory
    5. Returns metadata for all generated images

    Args:
        prompt (str): The full advertisement prompt built by prompt_builder.
        negative_prompt (str): Tokens describing what to avoid.
        model_choice (str): Key from MODELS dict ("1", "2", or "3").
        width (int): Desired image width in pixels.
        height (int): Desired image height in pixels.
        num_images (int): Number of images to generate (1-4).
        seed (int, optional): Base seed for reproducibility.

    Returns:
        list: List of dicts with image metadata:
              [{"id", "filename", "path", "width", "height", "model"}]
    """
    # Ensure output directory exists
    ensure_output_dir()

    # Clamp dimensions to model limits
    width, height = clamp_dimensions(width, height)

    # Limit number of images to maximum allowed
    num_images = min(num_images, MAX_IMAGES_PER_REQUEST)

    # Resolve model choice to API parameters
    model_info = MODELS.get(model_choice, MODELS["1"])
    provider = model_info["provider"]
    api_model = model_info["api_model"]
    model_name = model_info["name"]

    print("\n  Model: {}".format(model_name))
    print("  Provider: {}".format(provider.capitalize()))
    print("  Dimensions: {}x{}".format(width, height))
    print("  Generating {} image(s)...\n".format(num_images))

    results = []

    for i in range(num_images):
        # Use incremented seed for each image to get variety
        current_seed = (seed + i) if seed is not None else None

        try:
            print("  [{}/{}] Generating...".format(i + 1, num_images))

            # Route to the correct provider based on model config
            if provider == "huggingface":
                # Use Hugging Face Inference API for SDXL
                image = generate_huggingface(
                    prompt, api_model, width, height,
                    negative_prompt=negative_prompt,
                    seed=current_seed,
                )
            else:
                # Use Pollinations.ai API for FLUX / SDXL Turbo
                image = generate_pollinations(
                    prompt, api_model, width, height, current_seed
                )

            # Create a unique filename with timestamp and model tag
            file_id = uuid.uuid4().hex[:12]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "ad_{}_{}_{}.png".format(timestamp, model_info["key"], file_id)
            filepath = os.path.join(OUTPUT_DIR, filename)

            # Save the generated image as PNG
            image.save(filepath, "PNG")

            # Store metadata for this image
            results.append({
                "id": file_id,
                "filename": filename,
                "path": filepath,
                "width": image.width,
                "height": image.height,
                "model": model_name,
            })

            print("  [{}/{}] Saved: {}".format(i + 1, num_images, filename))

        except Exception as e:
            print("  [{}/{}] ERROR: {}".format(i + 1, num_images, str(e)))

    return results


def compare_models(prompt, negative_prompt="", width=1024, height=1024, seed=42):
    """
    Generate images using both SDXL (Hugging Face) and FLUX (Pollinations)
    for side-by-side comparison.

    This function demonstrates the use of two distinct LLMs from two different
    providers by generating one image from each model using the same prompt
    and seed, allowing direct comparison of outputs.

    Args:
        prompt (str): The advertisement prompt.
        negative_prompt (str): Tokens describing what to avoid.
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        seed (int): Random seed for reproducibility (default: 42).

    Returns:
        list: List of dicts with image metadata from both models.
    """
    print("\n" + "=" * 60)
    print("  MULTI-MODEL COMPARISON")
    print("  SDXL (Hugging Face) vs FLUX (Pollinations.ai)")
    print("=" * 60)

    all_results = []

    # Generate with Model 1: SDXL via Hugging Face
    print("\n--- Model 1: Stable Diffusion XL (Hugging Face) ---")
    results_sdxl = generate_images(
        prompt=prompt, negative_prompt=negative_prompt,
        model_choice="1",
        width=width, height=height, num_images=1, seed=seed
    )
    all_results.extend(results_sdxl)

    # Generate with Model 2: FLUX via Pollinations.ai
    print("\n--- Model 2: FLUX (Pollinations.ai) ---")
    results_flux = generate_images(
        prompt=prompt, negative_prompt=negative_prompt,
        model_choice="2",
        width=width, height=height, num_images=1, seed=seed
    )
    all_results.extend(results_flux)

    print("\n  Comparison complete! {} images generated.".format(len(all_results)))
    return all_results
