from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

image_folder = Path("images")
output_file = Path("image_contact_sheet.jpg")

files = sorted([
    f for f in image_folder.iterdir()
    if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".JPG".lower()]
])

thumb_width = 180
thumb_height = 180
label_height = 35
columns = 5
rows = math.ceil(len(files) / columns)

sheet = Image.new(
    "RGB",
    (columns * thumb_width, rows * (thumb_height + label_height)),
    "white"
)

draw = ImageDraw.Draw(sheet)

for i, file in enumerate(files):
    try:
        img = Image.open(file).convert("RGB")
        img.thumbnail((thumb_width - 10, thumb_height - 10))

        x = (i % columns) * thumb_width
        y = (i // columns) * (thumb_height + label_height)

        img_x = x + (thumb_width - img.width) // 2
        img_y = y + 5

        sheet.paste(img, (img_x, img_y))

        draw.text(
            (x + 5, y + thumb_height),
            f"{i + 1}: {file.name}",
            fill="black"
        )

    except Exception as e:
        print(f"Could not process {file}: {e}")

sheet.save(output_file, quality=90)

print(f"✅ Contact sheet created: {output_file}")
print(f"Total images: {len(files)}")
