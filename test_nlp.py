from app import nlp_utils

# Corpus simplu
questions = [
    "cum te numesti",
    "ce este bodai",
    "what can you do"
]

# Tokenizare corpus
docs = [nlp_utils.tokenize(q) for q in questions]

# Construim vocabular + DF
vocab, df, N = nlp_utils.build_tfidf(docs)

# Calcul TF-IDF pentru corpus
corpus_vectors = [nlp_utils.tfidf_vector(doc, vocab, df, N) for doc in docs]

# Simulăm o întrebare nouă
query = "Cum te numești?"
tokens = nlp_utils.tokenize(query)
query_vec = nlp_utils.tfidf_vector(tokens, vocab, df, N)

# Calculăm similaritatea cosinus între query și fiecare întrebare din corpus
for q, vec in zip(questions, corpus_vectors):
    score = nlp_utils.cosine_sim(query_vec, vec)
    print(f"Query='{query}' vs Corpus='{q}' => Score={score:.3f}")
