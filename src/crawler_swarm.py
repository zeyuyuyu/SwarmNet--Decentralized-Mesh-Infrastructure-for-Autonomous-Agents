import asyncio
import aiohttp
from collections import defaultdict
import time
from typing import List, Dict, Set

class CrawlerSwarm:
    def __init__(self, max_concurrent: int = 10, rate_limit_per_domain: int = 5):
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit_per_domain
        self.active_crawlers = 0
        self.domain_timestamps: Dict[str, List[float]] = defaultdict(list)
        self.seen_urls: Set[str] = set()
        self.session = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def can_crawl_domain(self, domain: str) -> bool:
        """Check if domain can be crawled based on rate limiting"""
        now = time.time()
        self.domain_timestamps[domain] = [t for t in self.domain_timestamps[domain] if now - t < 60]
        return len(self.domain_timestamps[domain]) < self.rate_limit

    async def crawl_url(self, url: str):
        """Crawl a single URL with rate limiting and error handling"""
        if url in self.seen_urls:
            return None
        
        self.seen_urls.add(url)
        domain = url.split('/')[2]
        
        while not self.can_crawl_domain(domain):
            await asyncio.sleep(1)
        
        try:
            self.domain_timestamps[domain].append(time.time())
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            return None

    async def process_batch(self, urls: List[str]) -> List[str]:
        """Process a batch of URLs with concurrency control"""
        await self.init_session()
        results = []
        
        async def worker(url):
            self.active_crawlers += 1
            try:
                result = await self.crawl_url(url)
                if result:
                    results.append(result)
            finally:
                self.active_crawlers -= 1

        tasks = []
        for url in urls:
            while self.active_crawlers >= self.max_concurrent:
                await asyncio.sleep(0.1)
            tasks.append(asyncio.create_task(worker(url)))

        await asyncio.gather(*tasks)
        return results

    @staticmethod
    def extract_urls(html: str) -> List[str]:
        """Extract URLs from HTML content"""
        # Basic URL extraction - can be enhanced with proper HTML parsing
        import re
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', html)
        return urls

    async def crawl(self, start_urls: List[str], max_depth: int = 3):
        """Main crawling method with depth control"""
        current_urls = start_urls
        all_results = []

        for depth in range(max_depth):
            results = await self.process_batch(current_urls)
            all_results.extend(results)

            new_urls = []
            for result in results:
                new_urls.extend(self.extract_urls(result))

            current_urls = list(set(new_urls) - self.seen_urls)
            if not current_urls:
                break

        await self.close()
        return all_results