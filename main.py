from pathlib import Path, PurePath
import datetime
import pytz
import shutil
import logging
from PIL import Image, ExifTags
import hashlib
import json
from io import BytesIO

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
        files = [x for x in dir_list if not x.is_dir() and PurePath(x).match('*.txt') is False]
        catalog_files([x for x in dir_list if x not in files and x.is_dir()], catalog)
        for file in files:
            with open(file, 'rb') as f:
                data = f.read()
                digest = hashlib.md5(data).hexdigest()
            path = PurePath(file).relative_to(DEFAULT_TARGET_ROOT)
            current = catalog.get(digest)
            if catalog.get(digest) is not None:
                logging.info(f'File with hash {digest} already exists at {current}, adding {path}')
                current.append(path)
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

def copy_files(dirs, catalog=None, paths=None):
    if catalog is None:
        catalog = {}
    if paths is None:
        paths = []

    logging.debug(f'Got {len(dirs)} directories.')
    for d in dirs:
        for file in sorted(d.glob('*')):
            # TODO: caculate file index from catalog
            # rercurse if dir
            if file.is_dir():
                logging.debug(f'Running copy_files for {file}.')
                copy_files([file,])

            ext = _get_file_ext(file)
            if ext not in ['avi', 'pdn', 'jpg', 'arw', 'mov', 'mp4', 'tif', 'xcf', 'm2ts', 'png', 'mts']:
                logging.debug(f'{file} has wrong file extension, skipping.')
                continue

            # check if already copied
            with open(file, 'rb') as f:
                bb = BytesIO(f.read())
            digest = hashlib.md5(bb.read()).hexdigest()
            bb.seek(0)
            if digest in catalog.keys():
                logging.info(f'{digest} found in catalog, skip.')
                continue

            # TODO: ugly
            try:
                img = Image.open(bb)
            except:
                dt = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=pytz.timezone('America/New_York'))
                logging.exception(f'Failed to open file as image {str(file)}, using {dt}.')
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

            idx = 0
            if dest.exists() is False:
                logging.debug(f'{dest} does not exist, creating. ')
                dest.mkdir(parents=True)
            else:
                matched = [x for x in catalog_paths if x.match(f'{date_str}/{ext}/*')]
                if matched:
                    last_idx = matched[-1].stem[-6:]
                    idx = int(last_idx) + 1

            dest_file = dest / f'{date_str}_{idx:06}.{ext}'
            logging.debug(f'Copying {str(file)} to {str(dest_file)}')
            try:
                shutil.copy2(file, dest_file)
                global counter
                counter += 1
            except PermissionError as err:
                logging.exception(f'Failed to copy {str(file)}, Continuing.')
                continue


def get_catalog(catalog_path):
    if catalog_path.exists() is False:
        logging.info(f'Could not find {catalog_path}.')
        return None

    with open(catalog_path, 'r') as f:
        try:
            catalog = json.load(f)
        except json.JSONDecodeError:
            logging.exception(f'Failed to decode {catalog_path}.')
            return None

    return catalog


if __name__ == '__main__':
    catalog = get_catalog(Path('catalog.txt'))
    print(len(catalog))
    catalog_paths = []
    for paths in catalog.values():
        catalog_paths.extend([PurePath(x) for x in paths])
    print(len(catalog_paths))
    # copy_files([Path(DEFAULT_ROOT_PATH) / 'test'], catalog, catalog_paths)