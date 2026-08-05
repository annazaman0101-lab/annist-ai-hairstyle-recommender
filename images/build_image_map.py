import pandas as pd
from pathlib import Path

# Load your dataset
csv_path = Path("data/hairmatch_metadata_143.csv")
df = pd.read_csv(csv_path)

# Get all image files
image_folder = Path("images")
image_files = sorted([
    f for f in image_folder.iterdir()
    if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
])

print(f"CSV records: {len(df)}")
print(f"Images found: {len(image_files)}")

# Show the first 20 records and images
print("\nCSV hairstyles:")
for i, row in df.head(20).iterrows():
    print(f"{i + 1}. {row['hairstyle_label']}")

print("\nFirst 20 images:")
for i, image in enumerate(image_files[:20], 1):
    print(f"{i}. {image.name}")

print("\n✅ Image inspection complete.")
