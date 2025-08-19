import os
import json
from PIL import Image
import exifread
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
            orientation = info.get('orientation') or None
            aspect_ratio = round(width / height, 4) if height else None
            exif = get_exif_data(img_path)
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
                'exif_make': exif.get('Image Make'),
                'exif_model': exif.get('Image Model'),
                'exif_datetime': exif.get('EXIF DateTimeOriginal'),
                'all_exif_json': json.dumps(exif, ensure_ascii=False),
            }
    except Exception as e:
        print(f"Error reading {img_path}: {e}")
        return None


