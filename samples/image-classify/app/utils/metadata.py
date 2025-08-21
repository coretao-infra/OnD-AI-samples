# Canonical function to list all available profiles and their fields
def get_all_profiles():
    """
    Return a dictionary mapping profile names to lists of field names, based on the canonical schema.
    """
    schema_path = NORMALIZE_SCHEMA_PATH
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    profiles = {}
    for field in schema['fields']:
        for prof in field['profiles']:
            profiles.setdefault(prof, []).append(field['name'])
    return profiles
import os
import json
from PIL import Image
from .config import NORMALIZE_SCHEMA_PATH

def get_profile_fields(profile_name, schema_path=None):
    """
    Return the list of field names for a given profile, using the schema path from config by default.
    """
    if schema_path is None:
        schema_path = NORMALIZE_SCHEMA_PATH
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    return [field['name'] for field in schema['fields'] if profile_name in field['profiles']]

def extract_metadata(input_dir, profile):
    """
    Canonical, config-driven, profile-based metadata extraction.
    The profile argument is required and must be a valid canonical profile name.
    """
    profile_fields = set(get_profile_fields(profile))
    records = []
    for root, _, files in os.walk(input_dir):
        for fname in files:
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                fpath = os.path.join(root, fname)
                meta = get_image_metadata(fpath, input_dir)
                if meta:
                    filtered = {k: v for k, v in meta.items() if k in profile_fields}
                    records.append(filtered)
    return records



    # REMOVED: exifread logic. Use only Pillow for EXIF extraction.

def get_image_orientation(img_path):
    """
    Canonically extract orientation from EXIF (PIL or exifread) for a given image path.
    Returns int or None.
    """
    orientation = None
    try:
        with Image.open(img_path) as img:
            exif_pil = img.getexif() if hasattr(img, 'getexif') else {}
            orientation = exif_pil.get(274)
    except Exception:
        pass
    if orientation is None:
        exif_data = get_exif_data(img_path)
        raw = exif_data.get('Image Orientation') or exif_data.get('Orientation')
        if raw:
            digits = ''.join(ch for ch in raw if ch.isdigit())
            orientation = int(digits) if digits else None
    return orientation

def get_image_metadata(img_path, input_dir):
    try:
        with Image.open(img_path) as img:
            width, height = img.size
            mode = img.mode
            info = img.info
            format = img.format
            dpi = info.get('dpi', (None, None))
            # Use only Pillow for EXIF extraction
            exif_pil = img.getexif() if hasattr(img, 'getexif') else {}
            orientation = exif_pil.get(274)
            def safe_num(val):
                # Handles PIL IFDRational, tuple, or other non-serializable types
                try:
                    if val is None:
                        return None
                    # IFDRational and similar
                    if hasattr(val, 'numerator') and hasattr(val, 'denominator'):
                        return float(val)
                    # tuple of numbers
                    if isinstance(val, tuple):
                        return tuple(safe_num(x) for x in val)
                    # numpy types, etc.
                    if hasattr(val, 'item'):
                        return val.item()
                    return val
                except Exception:
                    return str(val)

            bit_depth = img.bits if hasattr(img, 'bits') else None
            aspect_ratio = round(width / height, 4) if height else None
            stat = os.stat(img_path)
            rel_path = os.path.relpath(img_path, input_dir)
            parent_folder = os.path.basename(os.path.dirname(img_path))
            return {
                'filename': os.path.basename(img_path),
                'relative_path': rel_path,
                'parent_folder': parent_folder,
                'format': format,
                'width': safe_num(width),
                'height': safe_num(height),
                'aspect_ratio': safe_num(aspect_ratio),
                'mode': mode,
                'bit_depth': safe_num(bit_depth),
                'orientation': orientation,
                'dpi_x': safe_num(dpi[0]),
                'dpi_y': safe_num(dpi[1]),
                'file_size': os.path.getsize(img_path),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'compression': info.get('compression'),
                'exif_make': exif_pil.get(271),
                'exif_model': exif_pil.get(272),
                'exif_datetime': exif_pil.get(36867),
                'all_exif_json': json.dumps({k: str(v) for k, v in exif_pil.items()}, ensure_ascii=False),
            }
    except Exception as e:
        print(f"Error reading {img_path}: {e}")
        return None


