import asyncio
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class MultiURLCrawler:
    def __init__(
        self,
        headless: bool = True,
        cache_mode: CacheMode = CacheMode.BYPASS,
        run_timeout: Optional[int] = None,
    ):
        self.browser_conf = BrowserConfig(headless=headless)
        self.run_conf = CrawlerRunConfig(cache_mode=cache_mode)
        if run_timeout is not None:
            self.run_conf.run_timeout = run_timeout

    async def _fetch(self, crawler: AsyncWebCrawler, url: str) -> Optional[str]:
        result = await crawler.arun(url=url, config=self.run_conf)
        if result and result.success:
            return result.markdown.raw_markdown
        return None

    async def crawl_urls(self, urls: List[str]) -> List[Optional[str]]:
        async with AsyncWebCrawler(config=self.browser_conf) as crawler:
            return await asyncio.gather(
                *(self._fetch(crawler, url) for url in urls),
                return_exceptions=False
            )

# if __name__ == "__main__":

#     test_urls = ["https://www.geeksforgeeks.org/bubble-sort-algorithm/"]
#     crawler = MultiURLCrawler(headless=True, cache_mode=CacheMode.BYPASS)

#     results: List[Optional[str]] = asyncio.run(crawler.crawl_urls(test_urls))

#     print(f"Fetched {len(results)} result(s).")
#     for url, content in zip(test_urls, results):
#         print(f"\n--- Content for {url} ---")
#         print(content or "Failed to fetch")
