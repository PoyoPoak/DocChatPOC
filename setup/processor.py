import json
import os
import re
import numpy as np
from gensim.models import Word2Vec
from gensim.similarities import MatrixSimilarity
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from dotenv import load_dotenv

load_dotenv()

# nltk.download()

config = {
    "DOWNLOADS_PATH":       os.getenv("DOWNLOADS_PATH"),
    "MODEL_PATH":           os.getenv("MODEL_PATH"),
    "WORKING_DIR":          os.getenv("WORKING_DIR"),
}


def read_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = [line.strip().split(",") for line in f]
    return data


def read_docs(csv_data):
    document_list = []
    for row in csv_data:
        file_path = row[2]
        csv_data_idx = csv_data.index(row)
        document_content = ""
        
        # Read the document text from the file
        with open(f"{file_path}", "r", encoding="utf-8") as f:
            document_content = f.read()
    
        # Append tuple of document index and document text to the document list
        idx_txt = (csv_data_idx, document_content)
        document_list.append(idx_txt)
            
    return document_list


def process_text(idx_txt):
    text = idx_txt[1]
    
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
    model = Word2Vec(sentences=processed_documents, vector_size=500, window=6, min_count=0, workers=8)
    model.train(processed_documents, total_examples=model.corpus_count, total_words=model.corpus_total_words, epochs=100)
    model.save(config["MODEL_PATH"])
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
        
    print("Document vectors generated...")        
    return doc_vecs


def normalize(vec):
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec


def append_vec(csv_data, idx_txt, doc_vecs):
    # Convert doc_vecs to large string and replace commas with semicolons for CSV
    vec_strs = [json.dumps(vec.tolist()) for vec in doc_vecs]
    vec_strs = [vec.replace(",", ";") for vec in vec_strs]
    
    # Find the correct row in the csv_data and append the vector string
    for idx, vec_str in zip(idx_txt, vec_strs):
        csv_data[idx].append(vec_str)
        
        
def save_csv(data):
    with open(f"{config['DOWNLOADS_PATH']}/full_data.csv", "w", encoding="utf-8") as f:
        for row in data:
            f.write(",".join(map(str, row)) + "\n")
            
    print("CSV file saved with document vectorizations...")
    
    
def main():    
    print("Processing documents...")

    csv_path                = config["DOWNLOADS_PATH"] + "/data.csv"
    csv_data                = read_csv(csv_path)
    document_list           = read_docs(csv_data)
    processed_documents     = [process_text(document) for document in document_list]
    model                   = model_setup(processed_documents)
    doc_vecs                = vectorize_documents(processed_documents, model)
    doc_vecs                = np.array([normalize(vec) for vec in doc_vecs])
    index                   = MatrixSimilarity(doc_vecs, num_features=model.vector_size)

    append_vec(csv_data, [idx for idx, _ in document_list], doc_vecs)
    save_csv(csv_data)
    
    
if __name__ == "__main__":
    main()