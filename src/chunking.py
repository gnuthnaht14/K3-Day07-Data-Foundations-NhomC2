from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)
        # Zero-width split ngay sau các dấu kết thúc câu: ". ", "! ", "? ", ".\n"
        self._split_pattern = re.compile(r'(?<=\. )|(?<=! )|(?<=\? )|(?<=\.\n)')

    def _split_sentences(self, text: str) -> list[str]:
        raw_parts = self._split_pattern.split(text)
        sentences = [s.strip() for s in raw_parts]
        return [s for s in sentences if s]  # bỏ phần tử rỗng
    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        n = self.max_sentences_per_chunk
        chunks = []
        for i in range(0, len(sentences), n):
            group = sentences[i:i + n]
            chunks.append(" ".join(group).strip())

        return chunks

class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []

        # Base case: mảnh đã đủ nhỏ, không cần tách thêm
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Hết separator để dùng -> cắt cứng theo chunk_size
        if not remaining_separators:
            return [
                current_text[i:i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]
        rest = remaining_separators[1:]

        parts = list(current_text) if sep == "" else current_text.split(sep)

        # Đệ quy xuống sâu: mảnh nào vẫn còn dài thì tách tiếp bằng separator kế tiếp
        pieces: list[str] = []
        for i, part in enumerate(parts):
            # Gắn lại separator (trừ mảnh cuối) để không mất ký tự phân tách gốc
            if sep and i < len(parts) - 1:
                part = part + sep
            if not part:
                continue
            if len(part) > self.chunk_size:
                pieces.extend(self._split(part, rest))
            else:
                pieces.append(part)

        # Gom lên: ghép các mảnh nhỏ liền kề lại thành chunk gần đầy chunk_size
        return self._merge(pieces)

    def _merge(self, pieces: list[str]) -> list[str]:
        merged: list[str] = []
        current = ""
        for piece in pieces:
            if not current:
                current = piece
            elif len(current) + len(piece) <= self.chunk_size:
                current += piece
            else:
                merged.append(current)
                current = piece
        if current:
            merged.append(current)
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (mag_a * mag_b)

class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(c) for c in chunks]

            result[name] = {
                "chunks": chunks,
                "count": len(chunks),
                "avg_length": (sum(lengths) / len(lengths)) if lengths else 0.0,
                "max_chunk_size": max(lengths) if lengths else 0,
                "min_chunk_size": min(lengths) if lengths else 0,
            }

        return result
