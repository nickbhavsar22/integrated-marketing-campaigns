import socket
import ipaddress
import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urlparse, urljoin


def validate_url(url: str) -> None:
    """Validate URL to prevent SSRF attacks. Raises ValueError on invalid URLs."""
    if len(url) > 2048:
        raise ValueError("URL exceeds maximum length of 2048 characters")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme!r}. Only http/https allowed.")

    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    # Resolve hostname and check for private/reserved IPs
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve hostname: {hostname}")

    for family, _, _, _, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
            raise ValueError(f"URL resolves to private/reserved IP address: {ip}")


class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True
        self.converter.ignore_tables = False

    def scrape(self, url: str, depth: int = 1) -> str:
        """
        Scrapes a URL and optionally its top secondary pages.
        """
        validate_url(url)
        print(f"Scraping primary URL: {url}...")
        try:
            # Fetch the primary page's raw HTML first
            primary_html = self._fetch_raw_html(url)
            primary_markdown = self._convert_html_to_markdown(primary_html)

            if depth <= 0:
                return primary_markdown

            # Find deep links from the primary page's HTML
            deep_links = self._find_deep_links(url, primary_html)
            print(f"Found deep links: {deep_links}")
            
            combined_content = f"# Primary Page Summary\n{primary_markdown}\n\n"
            
            for link in deep_links[:3]: # Limit to 3 for speed
                validate_url(link)
                print(f"Scraping deep link: {link}...")
                page_html = self._fetch_raw_html(link)
                page_markdown = self._convert_html_to_markdown(page_html)
                combined_content += f"# Internal Page: {link}\n{page_markdown}\n\n"
                
            return combined_content
        except Exception as e:
            return f"Error during scrape: {str(e)}"

    def _fetch_raw_html(self, url: str) -> str:
        """Fetches the raw HTML content of a URL."""
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.text

    def _convert_html_to_markdown(self, html_content: str) -> str:
        """Converts HTML content to Markdown, cleaning it first."""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements, and navigation/footer
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        return self.converter.handle(str(soup))

    def _find_deep_links(self, base_url: str, html_content: str) -> list:
        """Simple heuristic to find high-value internal links."""
        validate_url(base_url)
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        domain = urlparse(base_url).netloc
        keywords = ['about', 'feature', 'service', 'product', 'solution', 'platform']
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Normalize
            full_url = urljoin(base_url, href)
            # Filter internal only
            if urlparse(full_url).netloc == domain:
                # Prioritize keywords
                if any(k in full_url.lower() for k in keywords):
                    if full_url not in links and full_url != base_url:
                        links.append(full_url)
        return list(set(links))

if __name__ == "__main__":
    # Test
    scraper = WebScraper()
    print(scraper.scrape("https://example.com"))
