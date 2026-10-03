import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Set up paths
SCRIPT_DIR = Path(__file__).parent.resolve()
DOWNLOADS_DIR = Path.home() / "Downloads"
LOG_FILE = SCRIPT_DIR / "file_organizer.log"

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi"],
    "Archives": [".zip", ".tar", ".gz", ".7z", ".rar"],
    "Executables": [".exe", ".msi", ".dmg", ".pkg", ".deb"],
}


def move_file(filepath: Path):
    """Sorts a single file into its target category folder and logs the action."""
    # Skip directories and incomplete download artifacts
    if filepath.is_dir() or filepath.suffix.lower() in [
        ".crdownload",
        ".tmp",
        ".download",
        ".part",
    ]:
        return

    file_ext = filepath.suffix.lower()
    moved = False

    for category, extensions in CATEGORIES.items():
        if file_ext in extensions:
            target_dir = DOWNLOADS_DIR / category
            target_dir.mkdir(exist_ok=True)
            shutil.move(str(filepath), str(target_dir / filepath.name))
            log_msg = f"MOVED: {filepath.name} -> {category}/"
            print(log_msg)
            logging.info(log_msg)
            moved = True
            break

    # Move unmapped extensions to 'Others'
    if not moved and file_ext:
        target_dir = DOWNLOADS_DIR / "Others"
        target_dir.mkdir(exist_ok=True)
        shutil.move(str(filepath), str(target_dir / filepath.name))
        log_msg = f"MOVED: {filepath.name} -> Others/"
        print(log_msg)
        logging.info(log_msg)


def organize_existing_files():
    """Scans and organizes files already present in the Downloads directory."""
    start_msg = "Starting scan of existing files in Downloads..."
    print(start_msg)
    logging.info(start_msg)

    for item in DOWNLOADS_DIR.iterdir():
        move_file(item)

    done_msg = "Existing files scan complete."
    print(done_msg)
    logging.info(done_msg)


class DownloadHandler(FileSystemEventHandler):

    def on_created(self, event):
        filepath = Path(event.src_path)
        time.sleep(1)  # Allow file write stream to finalize
        move_file(filepath)


if __name__ == "__main__":
    logging.info("--- File Manager Service Started ---")

    # Step 1: Clean up existing files
    organize_existing_files()

    # Step 2: Begin background file watching
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, str(DOWNLOADS_DIR), recursive=False)
    observer.start()

    watch_msg = (
        "Monitoring Downloads directory for new files... (Press Ctrl+C to stop)"
    )
    print(f"\n{watch_msg}")
    logging.info(watch_msg)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("--- File Manager Service Stopped ---")
    observer.join()