"""
Extract all base64-encoded images from New_main.ipynb and save them as PNG files
to an 'assets/training_plots/' directory.
"""
import json, base64, os

with open("New_main.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

os.makedirs("assets/training_plots", exist_ok=True)

img_index = 0
for cell_i, cell in enumerate(nb["cells"]):
    for output in cell.get("outputs", []):
        # Handle display_data and execute_result with image data
        data = output.get("data", {})
        if "image/png" in data:
            img_b64 = data["image/png"]
            if isinstance(img_b64, list):
                img_b64 = "".join(img_b64)
            img_bytes = base64.b64decode(img_b64)
            fname = f"assets/training_plots/plot_{img_index:02d}_cell{cell_i}.png"
            with open(fname, "wb") as f:
                f.write(img_bytes)
            print(f"Saved: {fname} ({len(img_bytes):,} bytes)")
            img_index += 1

print(f"\nTotal images extracted: {img_index}")
