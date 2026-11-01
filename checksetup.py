import torch
import chromadb
from sentence_transformers import SentenceTransformer

print("PyTorch version:", torch.__version__)
print("CUDA available (not strictly required since MiniLM runs fast on CPU):", torch.cuda.is_available())

# Initialize local embedding model to verify download
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded successfully! Test vector shape:", model.encode("Hello enterprise AI").shape)
