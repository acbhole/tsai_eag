import os
import pickle
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

CHUNK_SIZE = 1000 # Size of each chunk in characters
CHUNKS_PATH = "chunks.pickle" # Path to save the chunks
FAISS_INDEX_PATH = "faiss_index.bin" # Path to save the FAISS index
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5" # Model name for SentenceTransformer

class Memory:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
        self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
        self.chunks = [] # List to store chunks and their metadata
        self.load_index()

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits the input text into smaller chunks of size CHUNK_SIZE.

        Args:
            text (str): The input text to be chunked.

        Returns:
            List[str]: A list of text chunks.
        """
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE):
            chunks.append(text[i:i + CHUNK_SIZE])
        return chunks

    def embed(self, text: str) -> np.ndarray:
        # SentenceTransformer handles batching and tokenization internally
        embedding = self.model.encode(text)
        return embedding

    def add_to_index(self, url: str, chunks: List[str]):
        # Identify indices of existing chunks for the given URL
        old_indices = [i for i, c in enumerate(self.chunks) if c["url"] == url]

        # Rebuild the FAISS index excluding old chunks for the URL
        if old_indices:
            keep_indices = [i for i in range(len(self.chunks)) if i not in old_indices]
            self.chunks = [self.chunks[i] for i in keep_indices]
            if self.chunks:
                embeddings = np.array([c["embedding"] for c in self.chunks]).astype('float32')
                self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
                self.index.add(embeddings)
            else:
                self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())

        # Add new chunks and their embeddings
        for idx, chunk in enumerate(chunks):
            embedding = self.embed(chunk)
            self.index.add(np.array([embedding]).astype('float32'))
            self.chunks.append({"url": url, "chunk": chunk, "embedding": embedding, "position": idx})

        # Save the updated index and chunks
        self.save_index()

    def search(self, query: str, k: int = 5):
        """
        Searches for the top-k most similar chunks to the query.

        Args:
            query (str): The search query.
            k (int): The number of results to return.

        Returns:
            List[dict]: A list of chunks with metadata, excluding embeddings.
        """
        q_emb = self.embed(query)
        distances, indices = self.index.search(np.array([q_emb]).astype('float32'), k)
        results = []
        for i in indices[0]:  
            if 0 <= i < len(self.chunks):
                chunk = self.chunks[i].copy()
                if "embedding" in chunk:
                    del chunk["embedding"]
                results.append(chunk)
        return results

    def save_index(self):
        """
        Saves the FAISS index and chunks to their respective files.
        """
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

    def load_index(self):
        """
        Loads the FAISS index and chunks from their respective files.
        """
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            self.index = faiss.read_index(FAISS_INDEX_PATH)
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)
