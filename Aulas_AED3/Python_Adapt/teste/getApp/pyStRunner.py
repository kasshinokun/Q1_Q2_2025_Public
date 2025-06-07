import os
import sys
import subprocess
import importlib.util

def is_package_installed(package_name):
    """Check if a Python package is already installed"""
    return importlib.util.find_spec(package_name) is not None

def install_dependencies(package_lib):
    """Install required packages with confirmation and checks"""
    if is_package_installed(package_lib):
        print(f"✅ '{package_lib}' is already installed.")
        return
    
    print(f"\n⚠️ The package '{package_lib}' is not installed.")
    confirm = input(f"Do you want to install '{package_lib}'? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Installation cancelled.")
        return
    
    try:
        print(f"Installing '{package_lib}'...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_lib],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Successfully installed '{package_lib}'!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install '{package_lib}': {e.stderr}")

def run_script(script_name):
    """Run a Streamlit script with error handling"""
    if not os.path.exists(script_name):
        print(f"❌ Error: '{script_name}' not found in current directory.")
        return
    
    try:
        print(f"🚀 Running '{script_name}'...")
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", script_name],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running '{script_name}': {e}")
    except KeyboardInterrupt:
        print("\nScript stopped by user.")

def main():
    while True:
        print("\n🔹 Please select an option:")
        print("0) Exit")
        print("1) Install dependencies")
        print("2) Database Process")
        print("3) Run Huffman compression")
        print("4) Run LZW compression")
        print("5) Run Downloader")
        
        choice = input(">>> ").strip()
        
        options = {
            '0': lambda: sys.exit("👋 Exiting..."),
            '1': lambda: install_dependencies('streamlit'),
            '2': lambda: run_script('stInsertDataObjectPY.py'),
            '3': lambda: run_script('stHuffman.py'),
            '4': lambda: run_script('stLZWPY.py'),
            '5': lambda: run_script('getFromGitHub.py')
        }
        
        selected_function = options.get(
            choice,
            lambda: print("❌ Invalid choice. Please try again.")
        )
        selected_function()

if __name__ == "__main__":
    main()

 
