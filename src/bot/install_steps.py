import logging
import sys
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def install_pytorch(config):
#     """Install PyTorch from a custom index if specified."""
#     torch_index = config.get("torch_index")  # e.g. "https://download.pytorch.org/whl/nightly/rocm6.3"
#     if torch_index:
#         logger.info(f"Installing PyTorch from {torch_index}...")
#         subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch', '--index-url', torch_index])
#     else:
#         logger.info("Installing default PyTorch...")
#         subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'torch'])

def download_nltk_data():
    """Download required NLTK data."""
    try:
        import nltk
    except ImportError:
        logger.error("NLTK not installed. Please add it to requirements.txt, then rerun.")
        sys.exit(1)

    packages = ["punkt", "averaged_perceptron_tagger", "universal_tagset"]
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

if __name__ == "__main__":
    main()