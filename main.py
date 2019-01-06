from pathlib import Path, PurePath
import datetime
import pytz
import shutil
import logging
from PIL import Image, ExifTags
import hashlib
import json

DEFAULT_ROOT_PATH = 'z:/Morgan/pictures'
DEFAULT_TARGET_ROOT = 'z:/Morgan/pictures_target'

DEFAULT_DB = 'catalog.db'
counter = 0

log_path = 'run.log'
logging.basicConfig(filename=log_path, format='%(asctime)s: %(message)s', level=logging.DEBUG)

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


def catalog_files(dirs, catalog=None):
    if catalog is None:
        catalog = {}

    for d in dirs:
        dir_list = list(d.glob('*'))
        files = [x for x in dir_list if not x.is_dir() and 'last.txt' not in str(x)]
        catalog_files([x for x in dir_list if x not in files], catalog)
        for file in files:
            with open(file, 'rb') as f:
                data = f.read()
                digest = hashlib.md5(data).hexdigest()
            path = PurePath(file).relative_to(DEFAULT_TARGET_ROOT)
            current = catalog.get(digest)
            if catalog.get(digest) is not None:
                logging.info(f'File with hash {digest} already exists at {current}, adding {path}')
                current.append(file)
            else:
                logging.debug(f'Adding {digest} at {path}')
                catalog[digest] = [path, ]

    return catalog


def compare_results(comp):
    source = Path('z:/Morgan/') / 'new_pictures'
    source_files = [PurePath(x).stem for x in list(source.glob('*.*'))]

    count = 0
    for digest in comp.keys():
        if digest not in source_files:
            count += 1
            print(f'{comp[digest]} not found in {source}')

    print(len(source_files))
    print(count)

def copy_files(dirs):
    logging.debug(f'Got {len(dirs)} directories.')
    for d in dirs:
        for file in sorted(d.glob('*')):
            if file.is_dir():
                logging.debug(f'Running copy_files for {str(file)}.')
                copy_files([file,])

            ext = _get_file_ext(file)
            if ext not in ['avi', 'pdn', 'jpg', 'arw', 'mov', 'mp4', 'tif', 'xcf', 'm2ts', 'png', 'mts']:
                logging.debug(f'{str(file)} has wrong file extension, skipping.')
                continue

            # TODO: ugly
            try:
                img = Image.open(str(file))
            except:
                dt = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=pytz.timezone('America/New_York'))
                logging.debug(f'Failed to open file as image {str(file)}, using {dt}.')
            else:
                try:
                    exif_data = img._getexif()
                    exif_dt = exif_data[36867]
                except:
                    dt = datetime.datetime.fromtimestamp(file.stat().st_mtime, tz=pytz.timezone('America/New_York'))
                    logging.exception(f'Failed to get exif data from {file}, using {dt}.')
                else:
                    dt = datetime.datetime.strptime(exif_dt, '%Y:%m:%d %H:%M:%S')

            date_str = f'{dt.strftime("%Y_%m")}'

            dest = Path(DEFAULT_TARGET_ROOT) / date_str / ext
            last_file = dest / 'last.txt'

            if dest.exists() is False or last_file.exists() is False:
                logging.debug(f'{dest} or {last_file} does not exist, creating. ')
                idx = 0
                dest.mkdir(parents=True)
                with open(last_file, 'w') as f:
                    f.write(str(idx))
            else:
                with open(last_file, 'r+') as f:
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
                global counter
                counter += 1
            except PermissionError as err:
                logging.exception(f'Failed to copy {str(file)}, Continuing.')
                continue



if __name__ == '__main__':
    # dirs = [Path(DEFAULT_ROOT_PATH),]
    # logging.debug(f'Running copy_dirs for {",".join([str(x) for x in dirs])}')
    # copy_files(dirs)
    # logging.debug(f'Done. Copied {counter} files.')


    # root = PurePath(DEFAULT_TARGET_ROOT)
    # catalog = catalog_files([Path(DEFAULT_TARGET_ROOT),])
    # with open('catalog.txt', 'w') as f:
    #     f.write(json.dumps({k: [str(x) for x in v] for k, v in catalog.items()}))

    with open('catalog.txt', 'r') as f:
        data = json.loads(f.read())
    #
    #
    #
    compare_results(data)
    print(len(data))