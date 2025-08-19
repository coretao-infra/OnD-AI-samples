"""
Mark 1: Extract metadata from all images in the input directory and save to CSV for analysis.
"""



import os
import sys
import json
import argparse
import pandas as pd
from PIL import Image
import exifread
import logging

from app.utils.config import NORMALIZE_INPUT_DIR, NORMALIZE_META_OUT, NORMALIZE_SCHEMA_PATH



INPUT_DIR = os.path.abspath(NORMALIZE_INPUT_DIR)
META_OUT = os.path.abspath(NORMALIZE_META_OUT)
SCHEMA_PATH = os.path.abspath(NORMALIZE_SCHEMA_PATH)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_exif_data(img_path):
	try:
		with open(img_path, 'rb') as f:
			tags = exifread.process_file(f, details=True)
		return {k: str(v) for k, v in tags.items()}
	except Exception:
		return {}


def get_image_metadata(img_path, input_dir):
	try:
		with Image.open(img_path) as img:
			width, height = img.size
			mode = img.mode
			info = img.info
			format = img.format
			dpi = info.get('dpi', (None, None))
			bit_depth = img.bits if hasattr(img, 'bits') else None
			orientation = info.get('orientation') or None
			aspect_ratio = round(width / height, 4) if height else None
			exif = get_exif_data(img_path)
			# File system info
			stat = os.stat(img_path)
			rel_path = os.path.relpath(img_path, input_dir)
			parent_folder = os.path.basename(os.path.dirname(img_path))
			return {
				'filename': os.path.basename(img_path),
				'relative_path': rel_path,
				'parent_folder': parent_folder,
				'format': format,
				'width': width,
				'height': height,
				'aspect_ratio': aspect_ratio,
				'mode': mode,
				'bit_depth': bit_depth,
				'orientation': orientation,
				'dpi_x': dpi[0],
				'dpi_y': dpi[1],
				'file_size': os.path.getsize(img_path),
				'created_time': stat.st_ctime,
				'modified_time': stat.st_mtime,
				'compression': info.get('compression'),
				'exif_make': exif.get('Image Make'),
				'exif_model': exif.get('Image Model'),
				'exif_datetime': exif.get('EXIF DateTimeOriginal'),
				'all_exif_json': json.dumps(exif, ensure_ascii=False),
			}
	except Exception as e:
		print(f"Error reading {img_path}: {e}")
		return None



def get_profile_fields(profile_name, schema_path=SCHEMA_PATH):
	with open(schema_path, 'r', encoding='utf-8') as f:
		schema = json.load(f)
	return [field['name'] for field in schema['fields'] if profile_name in field['profiles']]

def main():
    parser = argparse.ArgumentParser(description="Extract image metadata with profile-based field selection.")
    parser.add_argument('--profile', type=str, default='basic', choices=['rich', 'basic', 'minimal'], help='Field profile to use (default: basic)')
    parser.add_argument('--output', type=str, default=META_OUT, help='Output CSV path')
    args = parser.parse_args()

    logging.info(f"INPUT_DIR: {INPUT_DIR}")
    logging.info(f"META_OUT: {args.output}")
    logging.info(f"SCHEMA_PATH: {SCHEMA_PATH}")
    logging.info(f"Profile: {args.profile}")

    if not os.path.exists(INPUT_DIR):
        logging.error(f"Input directory does not exist: {INPUT_DIR}")
        sys.exit(1)
    if not os.path.exists(SCHEMA_PATH):
        logging.error(f"Schema file does not exist: {SCHEMA_PATH}")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    records = []
    image_count = 0
    for root, _, files in os.walk(INPUT_DIR):
        for fname in files:
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                image_count += 1
                fpath = os.path.join(root, fname)
                logging.info(f"Processing image: {fpath}")
                meta = get_image_metadata(fpath, INPUT_DIR)
                if meta:
                    records.append(meta)
                else:
                    logging.warning(f"Failed to extract metadata for: {fpath}")
    logging.info(f"Total images found: {image_count}")
    logging.info(f"Total records extracted: {len(records)}")
    if not records:
        logging.error("No images found or failed to extract metadata.")
        print("No images found or failed to extract metadata.")
        sys.exit(1)
    df = pd.DataFrame(records)
    # Filter columns by profile
    profile_fields = get_profile_fields(args.profile)
    missing = [col for col in profile_fields if col not in df.columns]
    if missing:
        logging.warning(f"Some profile fields not found in data: {missing}")
        print(f"Warning: Some profile fields not found in data: {missing}")
    df_out = df[[col for col in profile_fields if col in df.columns]]
    df_out.to_csv(args.output, index=False)
    logging.info(f"Metadata for {len(df_out)} images written to {args.output} using profile '{args.profile}'")
    print(f"Metadata for {len(df_out)} images written to {args.output} using profile '{args.profile}'")


# Canonical script entry point
if __name__ == "__main__":
	main()

