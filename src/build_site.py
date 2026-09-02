import argparse
import os
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import hashlib, re


HTML_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
h1, h2 {{ margin: 0.2em 0; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
th {{ background: #f5f5f5; position: sticky; top: 0; }}
img.thumb {{ width: 120px; height: auto; }}
.small {{ color: #555; font-size: 0.95em; }}
.container {{ max-width: 1200px; margin: auto; }}
hr {{ margin: 24px 0; }}
</style>
</head>
<body>
<div class="container">
<h1>{title}</h1>
<p class="small">{subtitle}</p>
<hr/>
<h2>Chart: S[200] plotted in the order of O[200]</h2>
<p class="small">This plots file size (bytes) along images sorted by entropy ascending.</p>
<img src="s_along_o.png" alt="S along O chart" style="max-width:100%;height:auto"/>
<hr/>
<h2>Sortable Table</h2>
<p class="small">Images are shown in entropy order (O). Click column headers to sort (client-side).</p>
<table id="tbl">
<thead>
<tr>
<th>O</th>
<th>Thumb</th>
<th>Filename</th>
<th>Entropy (bits)</th>
<th>Size (bytes)</th>
<th>Dims</th>
<th># Unique Colors</th>
<th>Path</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<script>
// naive table sort
document.querySelectorAll("th").forEach((th, idx) => {{
  th.addEventListener("click", () => sortTable(idx);
}});
function sortTable(n) {{
  const table = document.getElementById("tbl");
  let switching = true, dir = "asc", switchcount = 0;
  while (switching) {{
    switching = false;
    const rows = table.rows;
    for (let i = 1; i < rows.length - 1; i++) {{
      let shouldSwitch = false;
      const x = rows[i].getElementsByTagName("TD")[n];
      const y = rows[i+1].getElementsByTagName("TD")[n];
      let xv = x.innerText || x.textContent;
      let yv = y.innerText || y.textContent;
      const xn = parseFloat(xv.replace(/[^0-9.\-]/g,""));
      const yn = parseFloat(yv.replace(/[^0-9.\-]/g,""));
      const isNum = !isNaN(xn) && !isNaN(yn);
      if (dir === "asc") {{
        if ((isNum && xn > yn) || (!isNum && xv.toLowerCase() > yv.toLowerCase())) {{
          shouldSwitch = true; break;
        }}
      }} else {{
        if ((isNum && xn < yn) || (!isNum && xv.toLowerCase() < yv.toLowerCase())) {{
          shouldSwitch = true; break;
        }}
      }}
    }}
    if (shouldSwitch) {{
      rows[i].parentNode.insertBefore(rows[i+1], rows[i]);
      switching = true;
      switchcount++;
    }} else {{
      if (switchcount === 0 && dir === "asc") {{ dir = "desc"; switching = true; }}
    }}
  }}
}}
</script>
</body>
</html>
"""

def make_thumb(src_path, thumb_path, max_w=300):
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    with Image.open(src_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if w > max_w:
            new_h = int(h * (max_w / w))
            im = im.resize((max_w, new_h))
        im.save(thumb_path, "JPEG", quality=85)


def safe_thumb_name(filename: str, o: int) -> str:
    # Short, sanitized name to avoid MAX_PATH and weird chars
    h = hashlib.md5(filename.encode("utf-8", "ignore")).hexdigest()[:10]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).split(".")[0][:24]
    return f"thumbs/{o:04d}_{stem}_{h}.jpg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="entropy.csv from compute_entropy.py")
    ap.add_argument("--site_dir", required=True, help="output directory for the website")
    ap.add_argument("--title", default="Image Entropy Results")
    ap.add_argument("--subtitle", default="O[200] (entropy order) vs S[200] (file size)")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    # Ensure O order
    if "O_rank_by_entropy" not in df.columns:
        df = df.sort_values("entropy_bits", ascending=True).reset_index(drop=True)
        df["O_rank_by_entropy"] = df.index + 1
    else:
        df = df.sort_values("O_rank_by_entropy", ascending=True).reset_index(drop=True)

    # Prepare site dirs
    os.makedirs(args.site_dir, exist_ok=True)
    imgdir = os.path.join(args.site_dir, "thumbs")
    os.makedirs(imgdir, exist_ok=True)

    # Chart: S along O index
    sizes = df["file_size_bytes"].values
    plt.figure()
    plt.plot(np.arange(1, len(sizes)+1), sizes, marker=".")
    plt.xlabel("O rank (by entropy, ascending)")
    plt.ylabel("File size (bytes)")
    plt.title("S[200] plotted along O[200]")
    chart_path = os.path.join(args.site_dir, "s_along_o.png")
    plt.savefig(chart_path, bbox_inches="tight", dpi=120)
    plt.close()

    # Build rows and thumbnails
    rows = []
    for _, r in df.iterrows():
        fp = r["filepath"]
        fn = r["filename"]
        o = int(r["O_rank_by_entropy"])
        ent = r["entropy_bits"]
        size_b = r["file_size_bytes"]
        dims = f"{int(r['width'])}×{int(r['height'])}" if not pd.isna(r['width']) else "—"
        nuniq = int(r["n_unique_colors"]) if not pd.isna(r["n_unique_colors"]) else 0

        rel_thumb = safe_thumb_name(fn,o)
        thumb_path = os.path.join(args.site_dir, rel_thumb)
        try:
            make_thumb(fp, thumb_path, max_w=300)
        except Exception as e:
            # keep going even if one thumb fails
            pass

        rows.append(f"<tr>"
                    f"<td>{o}</td>"
                    f"<td><img class='thumb' src='{rel_thumb}' alt='thumb'/></td>"
                    f"<td>{fn}</td>"
                    f"<td>{ent:.4f}</td>"
                    f"<td>{size_b}</td>"
                    f"<td>{dims}</td>"
                    f"<td>{nuniq}</td>"
                    f"<td class='small'>{os.path.basename(fp)}</td>"
                    f"</tr>")

    html = HTML_TMPL.format(title=args.title, subtitle=args.subtitle, rows="\n".join(rows))
    with open(os.path.join(args.site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote site to {args.site_dir}")

if __name__ == "__main__":
    main()
