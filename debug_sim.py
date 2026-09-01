from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
model = SentenceTransformer("all-MiniLM-L6-v2")
e1 = model.encode(["what is the otp?"])[0]
e2 = model.encode(["hey can you send me the netflix otp?"])[0]
print("Similarity:", cosine_similarity([e1], [e2])[0][0])
