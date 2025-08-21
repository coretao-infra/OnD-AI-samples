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
    actions_count = {}
    attr_stats = {}
    changed_attr_stats = {}
    log_entries = []
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
                log_entry = normalize_image(
                    input_path=in_path,
                    output_dir=img_dir,
                    log_path=log_path,
                    baseline=baseline_params
                )
                if log_entry:
                    log_entries.append(log_entry)
                    for action in log_entry.get('actions', []):
                        actions_count[action] = actions_count.get(action, 0) + 1
                    # Collect all attributes for stats
                    for k, v in log_entry.items():
                        if k in ['orig_size', 'final_size'] and isinstance(v, tuple):
                            attr_stats.setdefault(f'{k}_width', []).append(v[0])
                            attr_stats.setdefault(f'{k}_height', []).append(v[1])
                        elif k == 'final_size_bytes':
                            attr_stats.setdefault('final_file_size', []).append(v)
                        elif k not in ['input', 'output', 'actions', 'changed_attrs'] and isinstance(v, (int, float)):
                            attr_stats.setdefault(k, []).append(v)
                    # Collect changed attributes
                    for attr, change in log_entry.get('changed_attrs', {}).items():
                        changed_attr_stats.setdefault(attr, {'from': [], 'to': []})
                        changed_attr_stats[attr]['from'].append(change['from'])
                        changed_attr_stats[attr]['to'].append(change['to'])
                count += 1
            except Exception as e:
                logging.error(f"Failed to normalize {in_path}: {e}")
    logging.info(f"Completed normalization for {count} images.")
    print(f"Normalized {count} images. Logs written to {log_path}")

    # Print summary statistics
    def compute_stats(values):
        if not values:
            return {'min': None, 'max': None, 'avg': None}
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values)
        }

    print("\n===== NORMALIZATION SUMMARY =====")
    print(f"Total images processed: {count}\n")

    # Group actions by type and parameter (e.g., orientation:6, resize_width:2573, etc.)
    from collections import defaultdict
    action_type_counts = defaultdict(lambda: defaultdict(set))
    for idx, entry in enumerate(log_entries):
        for action in entry.get('actions', []):
            if ':' in action:
                act_type, param = action.split(':', 1)
                action_type_counts[act_type][param].add(idx)
            else:
                action_type_counts[action][''].add(idx)

    print("Actions applied:")
    for act_type in sorted(action_type_counts):
        total = sum(len(idxs) for idxs in action_type_counts[act_type].values())
        print(f"  {act_type}: {total} images")
        for param, idxs in sorted(action_type_counts[act_type].items()):
            if param:
                print(f"    - {param}: {len(idxs)} images")

    # Attribute changes (concise)
    print("\nChanged Attributes:")
    for attr, changes in changed_attr_stats.items():
        from_vals = changes['from']
        to_vals = changes['to']
        n_changed = len(from_vals)
        if n_changed == 0:
            continue
        if from_vals and isinstance(from_vals[0], tuple):
            for i, label in enumerate(['width', 'height']):
                from_comp = [v[i] for v in from_vals]
                to_comp = [v[i] for v in to_vals]
                from_stats = compute_stats(from_comp)
                to_stats = compute_stats(to_comp)
                print(f"  {attr}_{label}: {n_changed} images | before: avg={from_stats['avg']:.1f} | after: avg={to_stats['avg']:.1f}")
        else:
            from_stats = compute_stats(from_vals)
            to_stats = compute_stats(to_vals)
            print(f"  {attr}: {n_changed} images | before: avg={from_stats['avg']} | after: avg={to_stats['avg']}")

    # File size and pixel area totals and percent reduction
    orig_total = sum([entry['orig_size'][0]*entry['orig_size'][1] for entry in log_entries])
    final_total = sum([entry['final_size'][0]*entry['final_size'][1] for entry in log_entries])
    orig_bytes = None
    final_bytes = None
    if 'final_file_size' in attr_stats:
        final_bytes = sum(attr_stats['final_file_size'])
    try:
        orig_bytes = sum([os.path.getsize(entry['input']) for entry in log_entries])
    except Exception:
        pass
    print("\nPixel area before:  {:,}".format(orig_total))
    print("Pixel area after:   {:,}".format(final_total))
    if orig_bytes is not None:
        print("Bytes before:       {:,}".format(orig_bytes))
    if final_bytes is not None:
        print("Bytes after:        {:,}".format(final_bytes))
    if orig_bytes and final_bytes:
        reduction = 100 * (orig_bytes - final_bytes) / orig_bytes if orig_bytes else 0
        print(f"Bytes reduction:    {reduction:.1f}%")
    if orig_total and final_total:
        reduction = 100 * (orig_total - final_total) / orig_total if orig_total else 0
        print(f"Pixel area reduction: {reduction:.1f}%")
    print("===== END SUMMARY =====\n")


if __name__ == '__main__':
    main()
