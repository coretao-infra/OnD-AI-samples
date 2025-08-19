"""
Mark 1: Extract metadata from all images in the input directory and save to CSV for analysis.
"""



import os
import sys
import json
import argparse
import pandas as pd
import logging

from app.utils.config import NORMALIZE_INPUT_DIR, NORMALIZE_META_OUT
from app.utils.metadata import extract_metadata



INPUT_DIR = os.path.abspath(NORMALIZE_INPUT_DIR)
META_OUT = os.path.abspath(NORMALIZE_META_OUT)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def main():
    parser = argparse.ArgumentParser(description="Extract image metadata with canonical profile-based field selection.")
    parser.add_argument('--profile', type=str, required=True, help='Canonical field profile to use (required)')
    parser.add_argument('--output', type=str, default=META_OUT, help='Output CSV path')
    args = parser.parse_args()

    logging.info(f"INPUT_DIR: {INPUT_DIR}")
    logging.info(f"META_OUT: {args.output}")
    logging.info(f"Profile: {args.profile}")

    if not os.path.exists(INPUT_DIR):
        logging.error(f"Input directory does not exist: {INPUT_DIR}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    records = extract_metadata(INPUT_DIR, args.profile)
    image_count = len(records)
    logging.info(f"Total images found: {image_count}")
    if not records:
        logging.error("No images found or failed to extract metadata.")
        print("No images found or failed to extract metadata.")
        sys.exit(1)
    df = pd.DataFrame(records)
    df.to_csv(args.output, index=False)
    logging.info(f"Metadata for {len(df)} images written to {args.output} using profile '{args.profile}'")
    print(f"Metadata for {len(df)} images written to {args.output} using profile '{args.profile}'")


# Canonical script entry point
if __name__ == "__main__":
	main()

