"""
Utilities to download and process images.
"""
import os
from PIL import Image


def download_from_file(dir_path, resize=False):
    pass


def resize_img(fp, Y_size, delete=False):
    """Resize stored images."""
    img = Image.open(fp).convert('RGB')
    fnam, ext = os.path.splitext(fp)
    width, height = img.size
    imgResize = img.resize((int(width * (Y_size / height)), Y_size),
                           Image.ANTIALIAS)

    if delete:
        imgResize.save(fnam + '.jpg', 'JPEG', quality=90)
        os.remove(fp)
    else:
        imgResize.save(fnam + ' resized.jpg', 'JPEG', quality=90)


if __name__ == "__main__":
    resize_img('test.png', Y_size=540, delete=True)
