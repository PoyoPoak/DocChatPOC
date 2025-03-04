import json
import os
import re
import numpy as np

from gensim.models import Word2Vec
from gensim.similarities import MatrixSimilarity
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# nltk.download()

DATA_DIR = './DocumentProcessing/api'

queries = [
    # "patient allergies",
    # "How do I do a get request for a patient's allergies",
    # "How to update patient's insurance information",
    # "Update patient notes",
    "deleting a patient's insurance information",
]


# Walk through the data directory and read all the documents
def read_docs(DATA_DIR):
    document_list = []
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                document_list.append(f.read())
    return document_list


def process_text(text):
    stop_words = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    
    tokens = word_tokenize(text)
    lowered = [t.lower() for t in tokens]
    stopped = [t for t in lowered if t not in stop_words]
    stemmed = [stemmer.stem(t) for t in stopped]
    nummed = ['num' if t.isdigit() else t for t in stemmed]
    regex = [t for t in nummed if re.match(r'[^\W\d]*$', t)]
    
    return regex


def model_setup(processed_documents):
    model = Word2Vec(sentences=processed_documents, vector_size=300, window=6, min_count=0, workers=12)
    model.train(processed_documents, total_examples=model.corpus_count, total_words=model.corpus_total_words, epochs=100)
    
    # model.save("./DocumentProcessing/word2vec.model")
    # model = Word2Vec.load("word2vec.model")
    
    return model


def vectorize_documents(processed_documents, model):
    doc_vecs = []

    # For every review in the processed_reviews list vectorize the words 
    for document in processed_documents:
        word_vecs = []
    
        # For every word in the review, vectorize it and append it to the word_vecs list
        for word in document:
            try:
                vec = model.wv[word]
                word_vecs.append(vec)
            except KeyError:
                pass
        
        # If there are word vectors, average them to set as the document vector
        if word_vecs:
            document_avg = np.mean(word_vecs, axis=0)
        else:
            document_avg = np.zeros(model.vector_size)
        
        # Append the document vector to the doc_vecs list    
        doc_vecs.append(document_avg)
        
    return doc_vecs


def vectorize_queries(processed_queries, model):
    query_vecs = []

    # For every query in the processed_queries list vectorize the query
    for query in processed_queries:
        word_vecs = []
    
        for word in query:
            try:
                vec = model.wv[word] 
                word_vecs.append(vec)
            except KeyError:
                pass
    
        query_avg = np.mean(word_vecs, axis=0)
        query_vecs.append(query_avg)
    
    return query_vecs


def normalize(vec):
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec


def run_queries(document_list, queries, query_vecs, index):
    for q_idx, query_vec in enumerate(query_vecs):
        # Compute cosine similarities between the query vector and all document vectors
        sims = index[query_vec]
    
    # Get the indices of the top 3 documents (highest similarity scores)
        top3_ids = np.array(sims).argsort()[-3:][::-1]
    
        print("Query:", queries[q_idx])
        for idx in top3_ids:
            print("------------------------------------------------------------------------------------")
            print("{:.4f}: \"{}\"".format(sims[idx], document_list[idx]))
        print("\n")

# Read csv file of a table with columns: file_name, page_name, path, url
def read_csv(file_path="./DocumentProcessing/api/data.csv"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = [line.strip().split(",") for line in f]
    return data

# Save csv file of a table with columns: file_name, page_name, path, url, vector
def save_csv(data, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(f"{output_dir}/full_data.csv", "w", encoding="utf-8") as f:
        for row in data:
            f.write(",".join(map(str, row)) + "\n")

# Append column of vectors to csv file
def add_vectors_to_csv(csv_data, doc_vecs):
    # Convert doc_vecs to large string
    vec_strs = [json.dumps(vec.tolist()) for vec in doc_vecs]
    
    # Replace commas in the string with semicolons
    vec_strs = [vec.replace(",", ";") for vec in vec_strs]
    
    # Add the vector strings to the csv data to their respective rows
    for i, row in enumerate(csv_data):
        row.append(vec_strs[i])
        


document_list           = read_docs(DATA_DIR)
processed_queries       = [process_text(query) for query in queries]
processed_documents     = [process_text(document) for document in document_list]
model                   = model_setup(processed_documents)
doc_vecs                = vectorize_documents(processed_documents, model)
query_vecs              = vectorize_queries(processed_queries, model)
doc_vecs                = np.array([normalize(vec) for vec in doc_vecs])
index                   = MatrixSimilarity(doc_vecs, num_features=model.vector_size)
csv_data                = read_csv()

add_vectors_to_csv(csv_data, doc_vecs)
save_csv(csv_data, DATA_DIR)
# run_queries(document_list, queries, query_vecs, index)