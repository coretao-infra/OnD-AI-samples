"""
Script: normalize.py

Apply normalization to all images in the input directory using a previously generated baseline.
Saves normalized images and logs per-image actions.
"""
import os
import sys
import json
import argparse
import logging
import datetime
import shutil

from app.utils.config import (
    NORMALIZE_INPUT_DIR,
    NORMALIZE_OUTPUT_PATH,
    NORMALIZE_OUTPUT_LOG_PATH,
    NORMALIZE_BASELINE_OUTPUT_PATH
)
from app.utils.normalize_file import normalize_image

# Configure logging
def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    parser = argparse.ArgumentParser(
        description="Normalize images based on a baseline JSON and log actions."
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default=os.path.abspath(NORMALIZE_INPUT_DIR),
        help='Directory containing images to normalize'
    )
    parser.add_argument(
        '--baseline', '-b',
        type=str,
        default=os.path.abspath(NORMALIZE_BASELINE_OUTPUT_PATH),
        help='Path to baseline JSON file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=os.path.abspath(NORMALIZE_OUTPUT_PATH),
        help='Directory to write normalized images'
    )
    parser.add_argument(
        '--log', '-l',
        type=str,
        default=os.path.abspath(NORMALIZE_OUTPUT_LOG_PATH),
        help='Path to JSONL log file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable debug logging'
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    # Create timestamped subfolder under the image output directory to isolate each run
    timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    img_dir = os.path.join(args.output, timestamp)
    os.makedirs(img_dir, exist_ok=True)
    # Keep meta/log folder unchanged
    log_path = args.log
    logging.info(f"Normalizing images in: {args.input}")
    logging.info(f"Using baseline JSON: {args.baseline}")
    logging.info(f"Output images directory: {img_dir}")
    logging.info(f"Log file: {log_path}")

    # Validate input directory
    if not os.path.isdir(args.input):
        logging.error(f"Input directory not found: {args.input}")
        sys.exit(1)

    # Load baseline params
    try:
        with open(args.baseline, 'r', encoding='utf-8') as bf:
            baseline_params = json.load(bf)
        logging.info(f"Loaded baseline parameters: {baseline_params}")
    except Exception as e:
        logging.error(f"Failed to load baseline JSON: {e}")
        sys.exit(1)

    # Process images into this run folder
    count = 0
    for root, _, files in os.walk(args.input):
        for fname in files:
            # Skip hidden or non-image files by extension
            if fname.startswith('.'):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
                continue
            in_path = os.path.join(root, fname)
            try:
                normalize_image(
                    input_path=in_path,
                    output_dir=img_dir,
                    log_path=log_path,
                    baseline=baseline_params
                )
                count += 1
            except Exception as e:
                logging.error(f"Failed to normalize {in_path}: {e}")
    logging.info(f"Completed normalization for {count} images.")
    print(f"Normalized {count} images. Logs written to {log_path}")


if __name__ == '__main__':
    main()
