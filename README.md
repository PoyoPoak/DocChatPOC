# DocChat

DocChat is a proof-of-concept (POC) Windows console application designed to demonstrate a Retrieval-Augmented Generation (RAG) chatbot solution. It aims to streamline development workflows by improving API documentation accessibility and providing code generation aligned with the documentation. This project was developed over 10-12 hours so far.

## Known Bugs
- **NLTK Download Delays:** The initial download of NLTK data can be slow. Consider running the downloader in a separate session if needed.
- **Model Training Speed:** Training the word2vec model may take some time on slower machines. Lowering epochs may help, but could decrease accuracy.
- **Data Processing Errors:** If input files are missing or malformed, errors may occur during vectorization. Verify that the data gathering step has successfully stored all required documents.
- **query.py Script Packages:** Much of the python should be ran in the environment where the needed packages are available. The bot currently calls query outside of the env so the user must have all the packages installed locally for it to work.
- **Context Window Limitations:** With the method in which documents are processed, there is often extraneous text left over that is often irrelevant. With larger documents, multiple could potentially go over OpenAI's API token limitations.
- **Inaccurate References:** When checking out commits, model might not update and so retrieved results may be irrelevant and LLM can hallucinate answers.
- **Setup Issues:** There are C# packages that will be required, the setup instructions are not complete and may be missing steps.

## Overview & Vision

Develop a chatbot for developers that:
- **Improves documentation accessibility:** Curates API documentation and provides relevant usage examples.
- **Saves time:** Eliminates the need for developers to manually search and navigate through extensive documentation.
- **Leverages modern technology:** Uses C# for the core application with MySQL for data storage, while Python handles text scraping and processing for vectorization.

## Target Problem

- **Documentation Structure:** API documentation is often designed for universal referencing, not for quick, developer-focused searches.
- **Navigation Inefficiency:** Developers waste time searching for and navigating to specific documentation pages.
- **Context Deficiency:** Many documentation pages lack clear example usage and additional context.

## Benefits

- **Curated Documentation:** Presents API documentation in a developer-friendly format, including relevant examples.
- **Code Generation:** Uses the chatbot to generate code snippets based on the request, fully aligned with the API documentation.
- **Time Efficiency:** Reduces the time developers spend searching for documentation, allowing them to focus on coding.

## Deliverables

1. **Data Gathering**
   - Crawl and web scrape documentation.
   - Limit crawling to pages within specific parameters.
   - Extract and store the main content of each page as local files.
2. **Data Processing**
   - Read local files and process them for vectorization.
   - Train a word2vec model on the collected data.
   - Generate vector representations for each document.
3. **Index Storage**
   - Host a MySQL database to store vector embeddings along with file paths for retrieval.
4. **Chat Capabilities**
   - Enable interactive chatbot conversations that retain message history.
   - Allow the chatbot to retrieve and reference relevant documentation for context.

## Software Stack

- **Languages & Tools:** C#, Python, MySQL, Docker
- **Libraries & APIs:** word2vec, OpenAI’s LLM API, beautifulsoup4, NLTK

## Setup Instructions

### Docker & MySQL

1. **Pull the MySQL Docker image:**

   ```bash
   docker pull mysql
   ```

2. **Start Docker Container:**

   ```bash
   docker-compose up -d
   docker start mysql-server
   ```

3. **Log into MySQL (if needed):**

   ```bash
   docker run --rm -it --network mysql-net mysql mysql -h mysql-server -u admin -p
   ```

4. **View Documents:**

   ```sql
   USE documents;
   SELECT * FROM webpages;
   ```

5. **Reset Table:**

   ```sql
   TRUNCATE TABLE webpages;
   ```

### Environment Configuration

Create a `.env` file in the root of the project (use absolute paths where required) with the following template:

```ini
MODEL_PATH="/word2vec.model"
DOWNLOADS_PATH=""
WORKING_DIR=""

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=password
MYSQL_DATABASE=documents
```

Rename the file to `.env` and fill in the necessary values.

**BE SURE TO DO THE SAME FOR `launchSettings.json` FOR THE C# SCRIPTS** 

### Python Environment

1. **Setup Python Virtual Environment:**

   ```bash
   python -m venv "./env"
   ```

   - **WSL or Bash Terminal:**

     ```bash
     source env/Scripts/activate
     ```

   - **PowerShell:**

     ```powershell
     .\env\Scripts\activate 
     ```

2. **Install Python Packages:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install NLTK Data:**

   ```bash
   python -m nltk.downloader all
   ```

### Data Retrieval
Once your Python environment is setup, we're going to want to run `setup.py` to download our data and process it for our bot to ingest.

```bash
   python ./setup.py
   ```

## Remaining POC Work
For the purpose of skill demonstration, this POC is not of an optimal implementation. There is much that can be replaced, condensed, and streamlined. Whether that is as-is, or if it is ever to be a cloud hosted service and interactable via a web app.
- Word2vec vectorization is available in C# with the Microsoft.Spark.ML.Feature NuGet package available to download. Due to lack of time, I've decided to opt for the Python implementation.
- Considering information may be sensitive in other use cases, implementing a smaller locally running LLM would be ideal so information is not sent over the internet.
- Some scripts such as processor.py, crawler.py, and Chatbot.cs can be broken up into multiple files for organization and file structure convention.
- Much room for improvement in code efficiency as to redundant loops and etc, of course this was thrown together in short time.
