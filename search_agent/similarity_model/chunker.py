import re
from typing import List

class TextChunker:
    def __init__(self, max_chunk_size: int = 2500, overlap_sentences: int = 10):
        self.max_chunk_size = max_chunk_size
        self.overlap_sentences = overlap_sentences

    def split_by_paragraphs(self, text: str) -> List[str]:
        return re.split(r'\n{2,}', text.strip())

    def split_to_sentences(self, block: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', block.strip())
        if block and not re.search(r'[.!?]\s*$', block):
            sentences = sentences[:-1] + [sentences[-1] + '.']
        return sentences

    def chunk_text(self, text: str) -> List[str]:
        if not text:
            return []

        chunks: List[str] = []
        current_chunk = ""
        current_sentences: List[str] = []
        blocks = self.split_by_paragraphs(text)

        for block in blocks:
            if not block.strip():
                continue

            if len(block) <= self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                    current_sentences = []
                chunks.append(block)
                continue

            sentences = self.split_to_sentences(block)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > self.max_chunk_size and current_chunk:
                    chunks.append(current_chunk)
                    n = min(self.overlap_sentences, len(current_sentences))
                    overlap = current_sentences[-n:]
                    current_chunk = " ".join(s.strip() for s in overlap)
                    current_sentences = overlap.copy()

                sep = " " if current_chunk and not current_chunk.endswith(" ") else ""
                current_chunk += sep + sentence
                current_sentences.append(sentence)

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
