import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Set
from urllib.parse import urlparse

import aiohttp
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# Setup paths
MODULE_DIR = Path(__file__).parent
PROJECT_ROOT = MODULE_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data/raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self):
        # Load config
        with open(PROJECT_ROOT / "config.yaml") as f:
            config = yaml.safe_load(f)
            self.config = config.get('scraping', {})
        
        # Get settings
        self.js_sites = self.config.get('js_sites', {})
        self.domain_delays = {}
        
        self.headers = self.config.get('headers', {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Setup timeouts
        timeout_config = self.config.get('timeouts', {
            'connect': 5,
            'read': 15,
            'scrape': 30
        })
        self.timeout = aiohttp.ClientTimeout(
            connect=timeout_config['connect'],
            total=timeout_config['scrape']
        )
        
        if self.js_sites:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Initialize Selenium WebDriver."""
        options = Options()
        selenium_args = self.config.get('selenium', {}).get('args', [
            "--headless", "--no-sandbox", "--disable-dev-shm-usage"
        ])
        
        logger.info("Setting up Selenium with arguments:")
        for arg in selenium_args:
            logger.info(f"  {arg}")
            options.add_argument(arg)
        
        try:
            logger.info("Installing/finding Chrome driver...")
            driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            logger.info(f"Chrome driver path: {driver_path}")
            
            logger.info("Initializing Chrome driver...")
            self.driver = webdriver.Chrome(
                service=Service(driver_path),
                options=options
            )
            logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'msg'):
                logger.error(f"Driver message: {e.msg}")
            raise RuntimeError("Could not initialize Chrome driver")
    
    def __del__(self):
        """Cleanup selenium."""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def get_cached_urls(self) -> Set[str]:
        """Get set of URLs that have already been downloaded."""
        cached = set()
        for json_file in DATA_DIR.glob("*.json"):
            try:
                with open(json_file) as f:
                    metadata = yaml.safe_load(f)
                    if metadata and 'url' in metadata:
                        cached.add(metadata['url'])
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")
        return cached

    async def _wait_for_rate_limit(self, url: str):
        """Wait based on domain rate limiting from config."""
        domain = urlparse(url).netloc
        delays = self.config.get('delay', {})
        
        # Get delay for this domain, fallback to default_delay
        if isinstance(delays, dict):
            delay = delays.get(domain, self.config.get('default_delay', 0))
        else:
            # If delay is a number, use it as default delay
            delay = delays if isinstance(delays, (int, float)) else 0
        
        if delay > 0 and domain in self.domain_delays:
            time_since_last = datetime.now().timestamp() - self.domain_delays[domain]
            if time_since_last < delay:
                await asyncio.sleep(delay - time_since_last)
        
        self.domain_delays[domain] = datetime.now().timestamp()

    async def _fetch_with_selenium(self, url: str) -> bytes:
        """Fetch URL using Selenium for JavaScript-heavy sites."""
        domain = next((site for site in self.js_sites if site in url), None)
        if not domain:
            return None
            
        logger.info(f"Using Selenium for {url}")
        try:
            # Configure Chrome to wait for network idle
            self.driver.set_page_load_timeout(30)  # 30 second timeout
            self.driver.set_script_timeout(30)
            
            # Load the page and wait for network to be idle
            self.driver.get(url)
            self.driver.execute_script("return window.performance.timing.loadEventEnd")
            
            # Additional small wait for any final rendering
            await asyncio.sleep(2)
            
            page_source = self.driver.page_source
            if page_source:
                return page_source.encode()
            
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}")
            
        return None

    async def _fetch_url(self, url: str) -> Dict:
        """Fetch a single URL using appropriate method."""
        await self._wait_for_rate_limit(url)
        
        # Try Selenium first for configured sites
        if any(site in url for site in self.js_sites):
            content = await self._fetch_with_selenium(url)
            if content:
                return {
                    'url': url,
                    'content': content,
                    'content_type': 'text/html',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Otherwise use regular HTTP request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=self.timeout) as response:
                    response.raise_for_status()
                    content = await response.read()
                    return {
                        'url': url,
                        'content': content,
                        'content_type': response.headers.get('content-type', ''),
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _save_content(self, result: Dict) -> str:
        """Save downloaded content and metadata, return size in KB."""
        if not result:
            return "0"
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url = re.sub(r'[^\w\-_]', '_', result['url'])
        base_name = f"{safe_url}_{timestamp}"
        
        # Save content
        content_file = DATA_DIR / f"{base_name}.raw"
        with open(content_file, 'wb') as f:
            f.write(result['content'])
            
        # Save metadata
        metadata = {k: v for k, v in result.items() if k != 'content'}
        with open(DATA_DIR / f"{base_name}.json", 'w') as f:
            yaml.dump(metadata, f)
            
        return f"{content_file.stat().st_size / 1024:.1f}"

async def run_scrape():
    """Main function to run the scraper."""
    # Load URLs
    try:
        with open(PROJECT_ROOT / "urls.txt") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logger.error("urls.txt not found")
        return
    
    if not urls:
        logger.error("No URLs found in urls.txt")
        return
    
    # Initialize scraper
    scraper = Scraper()
    cached_urls = scraper.get_cached_urls()
    
    print(f"\nProcessing {len(urls)} URLs...")
    
    # Process URLs
    for url in urls:
        if url in cached_urls:
            print(f"• Cached: {url}")
            continue
            
        result = await scraper._fetch_url(url)
        if result:
            size_kb = scraper._save_content(result)
            print(f"✓ Downloaded: {url} ({size_kb}KB)")
        else:
            print(f"✗ Failed: {url}")

if __name__ == "__main__":
    asyncio.run(run_scrape())