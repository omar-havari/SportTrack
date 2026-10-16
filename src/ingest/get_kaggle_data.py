import sys
import shutil
from pathlib import Path
import filecmp
import pandas as pd
import logging
from log_setup import setup_logging

setup_logging()

# Checking number of arguments
if len(sys.argv) != 2:
    logging.error("Usage: python src/ingest/get_kaggle_data.py <path to csv>")
    sys.exit(1)

# Storing source path
src_path = Path(sys.argv[1])

# Validating source path
if not src_path.is_file():
    logging.error(f"Source file not found: {src_path}")
    sys.exit(1)

# Validating file type
if src_path.suffix.lower() != ".csv":
    logging.error(f"This type of file isn't supported: {src_path.name}")
    sys.exit(1)

# Storing destination path
dst_folder = Path("data/raw/kaggle")
dst_folder.mkdir(parents = True, exist_ok = True)
dst_path = dst_folder / src_path.name

# Checking if path exists and avoiding overwriting
if dst_path.exists():
    if filecmp.cmp(src_path, dst_path, shallow = False):
        logging.info(f"Already ingested, nothing copied: {dst_path}")
    else:
        logging.error(f"{dst_path} already exists and is different from {src_path}")
        logging.error("If this is a new version of the dataset, rename it or remove the old copy deliberately")
        sys.exit(1)
else:
    shutil.copy2(src_path, dst_path)
    logging.info(f"Copied {src_path.name} -> {dst_path}")

# Reading and displaying rows and columns
df = pd.read_csv(dst_path)
rows = len(df)
columns = len(df.columns)
logging.info(f"{dst_path.name} has {rows} rows and {columns} columns")