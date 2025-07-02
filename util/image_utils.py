import requests
from PIL import Image
from rembg import remove
import io
from util.logger import logger
import os

# Define a directory to cache processed images
PROCESSED_IMAGE_DIR = os.path.join("static", "processed_products")
if not os.path.exists(PROCESSED_IMAGE_DIR):
    os.makedirs(PROCESSED_IMAGE_DIR)


def remove_background(image_url: str) -> str:
    """
    Downloads an image, removes its background, saves it as a transparent PNG,
    and returns the path to the processed image.
    """
    try:
        # Create a unique filename based on the image URL
        image_name = os.path.basename(image_url).split('?')[0]
        # Ensure it's a format that can be handled, default to png
        base_name, _ = os.path.splitext(image_name)
        processed_filename = f"{base_name}.png"
        processed_image_path = os.path.join(PROCESSED_IMAGE_DIR, processed_filename)
        static_path = f"/static/processed_products/{processed_filename}"

        # If the image is already processed, return the cached path
        if os.path.exists(processed_image_path):
            logger.info(f"Using cached processed image: {static_path}")
            return static_path

        logger.info(f"Processing image: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()

        # Open the image and remove the background
        input_image = Image.open(io.BytesIO(response.content))
        output_image = remove(input_image)

        # Save the new image with a transparent background
        output_image.save(processed_image_path, "PNG")
        logger.info(f"Saved processed image to: {processed_image_path}")

        return static_path

    except Exception as e:
        logger.exception(f"Failed to process image from {image_url}: {e}")
        return None 