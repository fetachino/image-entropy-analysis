# Image Entropy and Compression Analysis

A Python analysis pipeline that measures true 24-bit RGB Shannon entropy, compares entropy ordering with compressed file size, and builds an interactive static results site.

## Pipeline

1. Recursively load JPEG images.
2. Count exact RGB color occurrences.
3. Calculate Shannon entropy: `H(X) = -sum(p(x) * log2(p(x)))`.
4. Sort images by entropy and compare the ordering with file size.
5. Export aggregate CSV results and build a browsable HTML report.

## Run

```console
python -m venv .venv
pip install -r requirements.txt
python src/compute_entropy.py --root data/images --out_csv results/entropy.csv
python src/build_site.py --csv results/entropy.csv --site_dir reports/site
```

## Result visualization

![File size mapped along entropy ordering](results/entropy-vs-file-size.png)

The analysis code and aggregate outputs are published; the third-party source-image collection and generated thumbnails are excluded.

## Course

CSCI 49000 AIT — Artificial Intelligence for IoT, Fall 2025.

## Author

Ahmed Balde
