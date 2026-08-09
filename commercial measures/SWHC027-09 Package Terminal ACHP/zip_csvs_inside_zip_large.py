import zipfile
import os
import shutil
import tempfile
import argparse
from pathlib import Path
from tqdm import tqdm


# Based on shutil.copyfileobj 
_WINDOWS = os.name == 'nt'
COPY_BUFSIZE = 1024 * 1024 if _WINDOWS else 64 * 1024
def copyfileobj_with_progress(fsrc, fdst, length=0, progress_func=None):
    # Helper function to copy file-like objects in chunks, with progress bar callback.
    if not length:
        length = COPY_BUFSIZE
    if progress_func is None:
        progress_func = lambda offset: None
    
    # Localize variable access to minimize overhead.
    fsrc_read = fsrc.read
    fdst_write = fdst.write
    
    while True:
        buf = fsrc_read(length)
        if not buf:
            break
        fdst_write(buf)
        progress_func(len(buf))  # delta offset

def zip_csvs_inside_zip_large(input_zip, output_filename_patter='{inputname}/{csvname}.zip', compresslevel=9, chunk_mb=16):
    """
    Create a new ZIP where each CSV inside the original ZIP is replaced by
    an individual nested ZIP file, without extracting CSVs to disk as normal files.
    Only non-nested CSV files are processed; the script does not look into ZIP subfolders or other file types.

    Example:
        input.zip
          file1.csv
          file2.csv

        output1.zip
          file1.csv
        output2.zip
          file2.csv

    Notes:
    - Designed for large CSVs. It streams data in chunks.
    - The output ZIP files are new; the input ZIP is not modified.
    """

    input_zip = Path(input_zip)
    chunk_size = chunk_mb * 1024 * 1024

    if not input_zip.exists():
        raise FileNotFoundError(f"Input ZIP not found: {input_zip}")

    csv_count = 0

    with zipfile.ZipFile(input_zip, "r") as zin:
        # build a list of CSV filenames from within the input ZIP, skipping directories and non-CSV files
        csvlist = [item.filename for item in zin.infolist() if not item.filename.endswith("/") and item.filename.lower().endswith('.csv')]
        #print(csvlist)
        print(f"CSV files found: {len(csvlist)}")

        for csvname in csvlist:
            print(f"Processing CSV: {csvname}")
            try:
                # Get the total size of the source file in bytes
                file_size = zin.getinfo(csvname).file_size
                output_zip = Path(output_filename_patter.format(inputname=input_zip.stem, csvname=csvname))
                if output_zip.exists():
                    raise FileExistsError(
                        f"Output ZIP already exists: {output_zip}\n"
                        "Delete it first or choose a different output name."
                    )
                output_zip.parent.mkdir(parents=True, exist_ok=True)
                print(f"Writing: {output_zip}")
                # Open the input CSV and output ZIP with context managers
                with (
                    zin.open(csvname, "r") as source,
                    zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED,
                                    compresslevel=compresslevel) as zout,
                ):
                    # Wrap the source file object with tqdm to track bytes read
                    with (
                        tqdm(total=file_size, unit='B', unit_scale=True, desc="Copying file") as pbar,
                        zout.open(csvname, "w") as target
                    ):
                        copyfileobj_with_progress(source, target, length=chunk_size, progress_func=pbar.update)
                output_zip_size = output_zip.stat().st_size
                compression_ratio = output_zip_size / file_size if file_size > 0 else 0
                print(f"Done. Output ZIP size: {output_zip_size} bytes, compression ratio: {compression_ratio:.2f}")
                csv_count += 1
            except Exception as e:
                print(f"Error processing {csvname}: {e}")
            break

    print("\nDone.")
    print(f"Created output ZIPs in folder: {output_zip.parent}")
    print(f"CSV files nested/zipped: {csv_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Zip each CSV inside an existing ZIP into its own nested ZIP without extracting CSVs to disk."
    )
    parser.add_argument("input_zip", help="Path to the original ZIP file")
    parser.add_argument(
        "--chunk-mb",
        type=int,
        default=16,
        help="Streaming chunk size in MB; default is 16",
    )

    args = parser.parse_args()

    zip_csvs_inside_zip_large(
        input_zip=args.input_zip,
        chunk_mb=args.chunk_mb,
    )


if __name__ == "__main__":
    main()
