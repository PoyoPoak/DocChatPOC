import sys
import numpy as np
import mysql.connector
import re
import os
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from gensim.models import Word2Vec
from gensim.similarities import MatrixSimilarity
from dotenv import load_dotenv

load_dotenv()

config = {
    "DOWNLOADS_PATH": os.getenv("DOWNLOADS_PATH"),
    "MODEL_PATH":     os.getenv("MODEL_PATH"),
    "WORKING_DIR":    os.getenv("WORKING_DIR"),
    
    "HOST":           os.getenv("MYSQL_HOST"),
    "PORT":           os.getenv("MYSQL_PORT"),
    "USER":           os.getenv("MYSQL_USER"),
    "PASSWORD":       os.getenv("MYSQL_PASSWORD"),
    "DATABASE":       os.getenv("MYSQL_DATABASE"),
}

if len(sys.argv) < 2:
    print("Usage: python query.py \"<query>\"")
    sys.exit(1)

query_text = sys.argv[1]

# Preprocess the query text
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
tokens = word_tokenize(query_text)
lowered = [t.lower() for t in tokens]
stopped = [t for t in lowered if t not in stop_words]
stemmed = [stemmer.stem(t) for t in stopped]    
nummed = ['num' if t.isdigit() else t for t in stemmed]
query_text = [t for t in nummed if re.match(r'[^\W\d]*$', t)]

model = Word2Vec.load(config["MODEL_PATH"])

# Vectorize the query by words
word_vecs = []
for word in query_text:
    try:
        vec = model.wv[word]
        word_vecs.append(vec)
    except KeyError:
        pass

if not word_vecs:
    print("No known words found in query.")
    sys.exit(1)

# Calculate the mean vector for the query
query_vec = np.mean(word_vecs, axis=0)

# Connect to the MySQL database
connection = mysql.connector.connect(
    host=config["HOST"],
    port=config["PORT"],
    user=config["USER"],
    password=config["PASSWORD"],
    database=config["DATABASE"],
)
cursor = connection.cursor()

# Query for file_path and vector_representation
sql = "SELECT file_path, vector_representation FROM webpages"
cursor.execute(sql)
results = cursor.fetchall()

def parse_vector(vector_str):
    # Remove the surrounding brackets
    vector_str = vector_str.strip()[1:-1]
    
    # Split the string using semicolons as delimiters
    elements = vector_str.split(';')
    vector = []
    for elem in elements:
        elem = elem.strip()
        if elem:
            # Ideally float not stored as string, but on time crunch we'll live with it
            try:
                vector.append(float(elem))
            except ValueError:
                print(f"Skipping non-numeric value: {elem}")
                pass
    return vector

docs = []
paths = []
for file_path, vector_str in results:
    vector = parse_vector(vector_str)
    docs.append(vector)
    paths.append(file_path)

docs = [list(enumerate(doc)) for doc in docs]
index = MatrixSimilarity(docs, num_features=model.vector_size)

# Compute the similarity scores between the query and all documents, get top 3
similarity_scores = index[query_vec]
top3_ids = np.array(similarity_scores).argsort()[-3:][::-1]
top3_paths = [paths[idx] for idx in top3_ids]

# print("Top 3 matching document paths:")
for path in top3_paths:
    print(path)

cursor.close()
connection.close()