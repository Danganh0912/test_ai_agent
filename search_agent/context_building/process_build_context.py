import sys
import os

current_dir = os.path.dirname(__file__)  
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

import asyncio
import re
from context_scraping.scrape import MultiURLCrawler
from search.serper_search import create_search_api
from similarity_model.similarity_search import SimilaritySearch
from similarity_model.chunker import TextChunker

class ProcessBuildContext:

    def __init__(self,
                 chunk_size: int = 1000,
                 overlap_sentences: int = 4,
                 embed_model_name: str = 'jinaai/jina-embeddings-v3',
                 serper_api_key: str = None,
                ):

        self.chunker = TextChunker(max_chunk_size=chunk_size,
                                   overlap_sentences=overlap_sentences)
        self.sim_search = SimilaritySearch(model_name=embed_model_name)
        self.search_api = create_search_api(serper_api_key)
        self.crawler = MultiURLCrawler()

    def build_context(self,
                      user_query: str,
                      top_k: int = 5) -> list[tuple[str, float]]:
        docs = []
        result = self.search_api.get_sources(user_query, num_results=3, stored_location="us")
        urls = []
        if result.success:
            organic = result.data.get('organic', [])
            for item in organic:
                url = item.get('link')
                if url:
                    urls.append(url)

        results = asyncio.run(self.crawler.crawl_urls(urls))

        for md in results:
            if md:
                docs.append(self._clean_markdown(md))

        all_chunks = []
        for doc in docs:
            chunks = self.chunker.chunk_text(doc)
            all_chunks.extend(chunks)

        retrieved = self.sim_search.get_retrieved_documents(user_query, all_chunks, top_k)
        return self._combine_content(retrieved)

    def _clean_markdown(self, md: str) -> str:
        md = md.replace('{', '{{').replace('}', '}}') 
        text = re.sub(r'```.*?```', '', md, flags=re.S)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r'[#>*\-_`]', '', text)
        return re.sub(r'\s+', ' ', text).strip()


    def _combine_content(self, results: list[tuple[str, float]]):
        if not results:
            return "No information is retrieved"

        aggregated = []
        for idx, (text, _) in enumerate(results, start=1):
            section = f"Information {idx}:\n{text.strip()}"
            aggregated.append(section)

        return "\n\n".join(aggregated)

