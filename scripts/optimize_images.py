"""Optional one-time PNG-to-JPEG encoding for generated opaque photographs.
Requires Pillow for this maintenance command only; the app has no dependencies.
No crop, colour adjustment, ingredient edit or resize is performed.
"""
from pathlib import Path
from PIL import Image
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--remove-png',action='store_true');args=parser.parse_args()
folder=Path(__file__).resolve().parents[1]/'assets/meals'
for source in sorted(folder.glob('menu-*.png')):
 target=source.with_suffix('.jpg')
 with Image.open(source) as image:
  image.convert('RGB').save(target,quality=86,optimize=True,progressive=True)
  with Image.open(target) as check:check.load();assert check.size==image.size
 if args.remove_png:source.unlink()
print('Verified JPEG images:',len(list(folder.glob('menu-*.jpg'))))
