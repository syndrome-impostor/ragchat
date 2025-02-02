import logging
import sys
import subprocess
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UNUSED - pytorch is installed in run.sh.
# def install_pytorch(config):
#     """Install PyTorch from a custom index if specified."""
#     torch_index = config.get("torch_index")  # e.g. "https://download.pytorch.org/whl/nightly/rocm6.3"
#     if torch_index:
#         logger.info(f"Installing PyTorch from {torch_index}...")
#         subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch', '--index-url', torch_index])
#     else:
#         logger.info("Installing default PyTorch...")
#         subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch'])

def get_webdriver_path():
    """Get the webdriver cache path."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / ".venv" / "webdrivers"

def setup_selenium():
    """Download and setup Selenium ChromeDriver."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        
        # Test driver installation and initialization
        logger.info("Installing ChromeDriver...")
        manager = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM)
        driver_path = manager.install()
        logger.info(f"ChromeDriver installed at: {driver_path}")
        
        # Test driver initialization
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=webdriver.chrome.service.Service(driver_path), options=options)
        driver.quit()
        logger.info("Selenium setup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup Selenium: {str(e)}")
        raise

def download_nltk_data():
    """Download required NLTK data."""
    try:
        import nltk
    except ImportError:
        logger.error("NLTK not installed. Please add it to requirements.txt, then rerun.")
        sys.exit(1)

    packages = ["punkt", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng", "universal_tagset", "punkt_tab"]
    for pkg in packages:
        logger.info(f"Downloading NLTK package: {pkg}")
        nltk.download(pkg)

def main():
    # # 1. Load config
    # import yaml
    # with open("config.yaml", "r") as f:
    #     config = yaml.safe_load(f)

    # # 2. Install PyTorch
    # if config.get("type") == "rocm":
    #     # or just rely on config.get("torch_index") if that covers it
    #     logger.info("Detected rocm type in config.")
    # install_pytorch(config)

    # 3. Install NLTK data
    download_nltk_data()
    
    # Setup Selenium
    setup_selenium()

if __name__ == "__main__":
    main()