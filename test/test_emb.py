import ollama

text = "This is a test mem to store in RAG. It should be vectorized and stored in the my_mem folder."
response = ollama.embeddings(model="nomic-embed-text", prompt=text)

print(f"vector length: {len(response['embedding'])}")
print(f"vector content: {response['embedding'][:5]}...")