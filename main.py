from pathlib import Path
import os
import datetime
import pytz
import shutil
import logging
from PIL import Image, ExifTags

DEFAULT_ROOT_PATH = 'z:/Morgan/pictures'
DEFAULT_TARGET_ROOT = 'z:/Morgan/pictures_target'

log_path = 'run.log'
logging.basicConfig(filename=log_path, level=logging.DEBUG)

def _get_file_ext(path):
    pth_str = str(path)
    idx = pth_str.rfind('.', ) + 1
    return pth_str[idx:].lower()


def dirwalk(root_path, dirs=[], exts=set(), files=[]):
    # root_path = Path(root)
    for pth in root_path.iterdir():
        if pth.is_dir():
            dirs.append(pth)
            dirwalk(pth, dirs, exts)
        else:
            exts.add(_get_file_ext(pth))
            files.append(pth)


    return dirs, exts, files


def copy_files(dirs):
    logging.debug(f'Got {len(dirs)} directories.')
    for d in dirs:
        for file in sorted(d.glob('*')):
            if file.is_dir():
                logging.debug(f'Running copy_files for {str(file)}.')
                copy_files([file,])

            ext = _get_file_ext(file)
            # if ext not in ['avi', 'pdn', 'jpg', 'arw', 'mov', 'mp4', 'tif', 'xcf', 'm2ts', 'png', 'mts']:
            if ext not in ['jpg']:
                logging.debug(f'{str(file)} has wrong file extension, skipping.')
                continue
            dt = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=pytz.timezone('America/New_York'))
            date_str = f'{dt.strftime("%Y_%m")}'

            img = Image.open(str(file))

            exif_data = img._getexif()
            tag = ExifTags.TAGS[36867]

            dest = Path(DEFAULT_TARGET_ROOT) / date_str / ext

            if dest.exists() is False:
                logging.debug(f'{dest} does not exist, creating. ')
                idx = 0
                dest.mkdir(parents=True)
                with open(dest / 'last.txt', 'w') as f:
                    f.write(str(idx))
            else:
                with open(dest / 'last.txt', 'r+') as f:
                    data = f.read()
                    last_idx = int(data)
                    idx = last_idx + 1
                    f.seek(0)
                    f.write(str(idx))
                    f.truncate()

            dest_file = dest / f'{date_str}_{idx:06}.{ext}'
            logging.debug(f'Copying {str(file)} to {str(dest_file)}')
            try:
                shutil.copy2(file, dest_file)
            except PermissionError as err:
                logging.exception(f'Failed to copy {str(file)}, Continuing.')
                continue


if __name__ == '__main__':
    # dirs, exts, files = dirwalk(Path(DEFAULT_ROOT_PATH))
    # print(f'Found {len(dirs)} directories')
    # print(f'Found {len(files)} files.')
    # print(exts)
    dirs = [Path(DEFAULT_ROOT_PATH) / '1-11-2016',]
    logging.debug(f'Running copy_dirs for {",".join([str(x) for x in dirs])}')
    copy_files(dirs)
