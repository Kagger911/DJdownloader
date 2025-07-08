import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
import platform

def print_banner():
    print("=" * 60)
    print(" 🎵 DJ Downloader Environment Setup")
    print("=" * 60)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_ffmpeg(ffmpeg_dir):
    ffmpeg_zip_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    ffmpeg_zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
    print("[*] Downloading FFmpeg...")

    def _progress(block_num, block_size, total_size):
        done = int(50 * block_num * block_size / total_size)
        sys.stdout.write('\r[%s%s]' % ('=' * done, ' ' * (50 - done)))
        sys.stdout.flush()
    urllib.request.urlretrieve(ffmpeg_zip_url, ffmpeg_zip_path, _progress)
    print("\n[*] Extracting FFmpeg...")
    with zipfile.ZipFile(ffmpeg_zip_path, 'r') as zip_ref:
        zip_ref.extractall(ffmpeg_dir)
    extracted_folders = [f for f in os.listdir(ffmpeg_dir) if os.path.isdir(os.path.join(ffmpeg_dir, f))]
    if not extracted_folders:
        raise RuntimeError("❌ FFmpeg extraction failed.")
    extracted_folder = extracted_folders[0]
    bin_path = os.path.join(ffmpeg_dir, extracted_folder, "bin")
    # Remove zip after extraction
    try: os.remove(ffmpeg_zip_path)
    except: pass
    return bin_path

def create_virtualenv(venv_path):
    print("[*] Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", venv_path])

def get_python_bin(venv_dir):
    # Platform agnostic
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        return os.path.join(venv_dir, "bin", "python")

def install_packages(venv_python):
    print("[*] Upgrading pip...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
    print("[*] Installing SpotDL, yt-dlp, and pyperclip...")
    subprocess.check_call([
        venv_python, "-m", "pip", "install",
        "spotdl",
        "yt-dlp",
        "pyperclip"
    ])

def patch_path_for_ffmpeg(venv_dir, ffmpeg_bin):
    # Update activate scripts for easy ffmpeg access in the venv
    if os.name == "nt":
        activate = os.path.join(venv_dir, "Scripts", "activate.bat")
        if os.path.isfile(activate):
            with open(activate, "a") as f:
                f.write(f'\nset PATH={ffmpeg_bin};%PATH%\n')
    else:
        activate = os.path.join(venv_dir, "bin", "activate")
        if os.path.isfile(activate):
            with open(activate, "a") as f:
                f.write(f'\nexport PATH="{ffmpeg_bin}:$PATH"\n')

def main():
    print_banner()

    # --- Optional: Ask for install location ---
    base_dir = os.path.join(os.getcwd(), "DJDownloader")
    print(f"[*] Installing to: {base_dir}")
    venv_dir = os.path.join(base_dir, "spotdl_venv")
    ffmpeg_dir = os.path.join(base_dir, "ffmpeg")
    config_file = os.path.join(base_dir, "djdownloader_paths.txt")
    ensure_dir(base_dir)
    ensure_dir(ffmpeg_dir)

    # --- Download FFmpeg ---
    ffmpeg_bin = download_ffmpeg(ffmpeg_dir)

    # --- Create Virtualenv ---
    create_virtualenv(venv_dir)
    venv_python = get_python_bin(venv_dir)

    # --- Install Packages ---
    install_packages(venv_python)

    # --- Patch PATH ---
    patch_path_for_ffmpeg(venv_dir, ffmpeg_bin)

    # --- Save config ---
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(f"VENV_PYTHON={venv_python}\n")
        f.write(f"FFMPEG_BIN={ffmpeg_bin}\n")

    print("\n✅ All done!")
    print(f"Virtual environment at: {venv_dir}")
    print(f"FFmpeg binaries at: {ffmpeg_bin}")
    print("\nTo activate your environment, run:")
    if os.name == "nt":
        print(f'    {venv_dir}\\Scripts\\activate.bat')
    else:
        print(f'    source {venv_dir}/bin/activate')
    print("Then run: python downloader_app.py")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        input("\nPress Enter to exit...")
