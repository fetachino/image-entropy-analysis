import argparse
import os
import sys
import pandas as pd
import numpy as np
from PIL import Image
from tqdm import tqdm

def list_images(root_dir):
    exts = {".jpg", ".jpeg", ".JPG", ".JPEG"}
    for base, _, files in os.walk(root_dir):
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in exts:
                yield os.path.join(base, f)

def image_entropy_rgb24(img_path):
    """Compute entropy over exact 24-bit RGB colors (no quantization)."""
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        arr = np.array(im, dtype=np.uint8)  # H x W x 3
    # pack RGB to uint32: R<<16 | G<<8 | B
    flat = arr.reshape(-1, 3).astype(np.uint32)
    packed = (flat[:,0] << 16) | (flat[:,1] << 8) | flat[:,2]
    # counts of unique colors
    uniq, counts = np.unique(packed, return_counts=True)
    total = counts.sum()
    p = counts.astype(np.float64) / float(total)
    # entropy base-2
    entropy = -np.sum(p * np.log2(p))
    return entropy, w, h, total, uniq.size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Root folder with JPG/JPEGs (recursively scanned)")
    ap.add_argument("--out_csv", required=True, help="Output CSV path (entropy.csv)")
    args = ap.parse_args()

    rows = []
    files = list(list_images(args.root))
    if not files:
        print(f"No JPEGs found in: {args.root}", file=sys.stderr)
        sys.exit(1)

    for fp in tqdm(files, desc="Computing entropy"):
        try:
            ent, w, h, npx, nuniq = image_entropy_rgb24(fp)
            size_bytes = os.path.getsize(fp)
            rows.append({
                "filepath": fp,
                "filename": os.path.basename(fp),
                "width": w,
                "height": h,
                "n_pixels": int(npx),
                "n_unique_colors": int(nuniq),
                "file_size_bytes": int(size_bytes),
                "entropy_bits": float(ent),
            })
        except Exception as e:
            rows.append({
                "filepath": fp,
                "filename": os.path.basename(fp),
                "width": np.nan,
                "height": np.nan,
                "n_pixels": np.nan,
                "n_unique_colors": np.nan,
                "file_size_bytes": os.path.getsize(fp) if os.path.exists(fp) else np.nan,
                "entropy_bits": np.nan,
            })
            print(f"[WARN] {fp}: {e}", file=sys.stderr)

    df = pd.DataFrame(rows)
    # sort by entropy to define O
    df_sorted = df.sort_values("entropy_bits", ascending=True).reset_index(drop=True)
    df_sorted["O_rank_by_entropy"] = df_sorted.index + 1

    df_sorted.to_csv(args.out_csv, index=False)
    print(f"Wrote {args.out_csv} with {len(df_sorted)} rows.")

if __name__ == "__main__":
    main()
