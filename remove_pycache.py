import os
import shutil

def clean_python_cache(start_path):
    removed_dirs = 0
    removed_files = 0

    for root, dirs, files in os.walk(start_path):
        if "__pycache__" in dirs:
            path = os.path.join(root, "__pycache__")
            shutil.rmtree(path, ignore_errors=True)
            print(f"Removed dir: {path}")
            removed_dirs += 1

        for file in files:
            if file.endswith(".pyc"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                    removed_files += 1
                except Exception as e:
                    print(f"Failed to remove {file_path}: {e}")

    print(f"\n✅ Removed {removed_dirs} __pycache__ folders")
    print(f"✅ Removed {removed_files} .pyc files")

if __name__ == "__main__":
    print(f"🔍 Cleaning Python cache from: {os.getcwd()}\n")
    clean_python_cache(os.getcwd())
