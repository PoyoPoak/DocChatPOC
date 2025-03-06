import csv
import mysql.connector
import os
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

def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS webpages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        file_name VARCHAR(255),
        page_name VARCHAR(255),
        file_path VARCHAR(255),
        url VARCHAR(255),
        vector_representation TEXT
    )
    """
    cursor.execute(create_table_query)
    
def reset_table(cursor):
    truncate_table_query = """
    TRUNCATE TABLE webpages
    """
    cursor.execute(truncate_table_query)
    create_table(cursor)

def main():
    print("Uploading index/vector table to MySQL database...")
    connection = mysql.connector.connect(
        host=config["HOST"],
        port=config["PORT"],
        user=config["USER"],
        password=config["PASSWORD"],
        database=config["DATABASE"]
    )
    cursor = connection.cursor()
    
    # Create the table if it doesn't already exist
    create_table(cursor)
    
    # Open and read the CSV file
    csv_path = config["DOWNLOADS_PATH"] + "/full_data.csv"
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        # Optionally skip the header row if your CSV file has one:
        # next(csvreader, None)
        for row in csvreader:
            # Check that the row has at least five columns
            if len(row) < 5:
                continue
            file_name = row[0].strip()
            page_name = row[1].strip()
            file_path = row[2].strip()
            url = row[3].strip()
            vector_representation = row[4].strip()  # storing as a string; you can parse it if needed

            insert_query = """
            INSERT INTO webpages (file_name, page_name, file_path, url, vector_representation)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (file_name, page_name, file_path, url, vector_representation))
    
    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()