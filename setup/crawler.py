import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import re
import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "START_URL":        "https://www.opendental.com/site/apispecification.html",
    "MAX_DEPTH":        2,
    "BLACKLIST":        [],
    "WHITELIST":        ["https://www.opendental.com/site/api"],
    "MODEL_PATH":       os.getenv("MODEL_PATH"),
    "DOWNLOADS_PATH":   os.getenv("DOWNLOADS_PATH"),
}

# Create the downloads directory if it does not exist
if not os.path.exists(config["DOWNLOADS_PATH"]):
    os.makedirs(config["DOWNLOADS_PATH"])

def clean_and_save(URL, content, DOWNLOADS_PATH):
    soup = BeautifulSoup(content, "html.parser")

    # Remove unwanted elements: script, style, noscript, nav, and aside
    for tag in soup.find_all(["script", "style", "noscript", "nav", "aside"]):
        tag.decompose()

    # Remove table-of-contents cell or div if present in subpages
    toc_text = soup.find(string=lambda x: x and "Table of Contents" in x)
    if toc_text:
        parsed = urlparse(url)
        page_name = parsed.path.rstrip('/').split('/')[-1] or "index"
        if page_name.lower() not in ("index", "manual"): 
            parent = toc_text.find_parent(["div", "td"])
            if parent:
                parent.decompose()
            else:
                toc_text.extract()

    # Remove top menu links like "Open Dental Home", "Search", and version selector if they remain
    for link_text in ["Open Dental Home", "Search"]:
        link = soup.find('a', string=lambda x: x and x.strip() == link_text)
        if link:
            link_parent = link.parent
            link.decompose()
            if link_parent and not link_parent.get_text(strip=True):
                link_parent.decompose()
                
    # Remove version list (e.g., "Manual v24.4 +v24.3 ...") if present
    version_line = soup.find(string=re.compile(r"Manual v\d+\.\d"))
    if version_line:
        parent = version_line.parent
        if parent:
            parent.decompose()
        else:
            version_line.extract()

    # Add bullet markers for list items to preserve list structure in text
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li", recursive=False):
            li.insert(0, "- ")
    for ol in soup.find_all("ol"):
        num = 1
        for li in ol.find_all("li", recursive=False):
            li.insert(0, f"{num}. ")
            num += 1

    # Extract text
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    
    # Remove empty lines and any residual unwanted lines
    cleaned_lines = []
    for line in lines:
        if not line:
            continue 
        cleaned_lines.append(line)
        
    # Join lines back together and collapse
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

    # Save the cleaned text to a file
    file_name = URL.split("/")[-1].split(".")[0]
    page_name = cleaned_text.split("\n")[0].replace(",", "")
    output_path = os.path.join(DOWNLOADS_PATH, file_name)
    
    # Save the cleaned text to a file, create if it does not exist
    with open(f"{output_path}", "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    return file_name, page_name

def save_csv_index(data, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(f"{output_dir}/data.csv", "w", encoding="utf-8") as f:
        for row in data:
            f.write(",".join(row) + "\n")


def crawl(START_URL=config["START_URL"], 
          MAX_DEPTH=config["MAX_DEPTH"], 
          BLACKLIST=config["BLACKLIST"], 
          WHITELIST=config["WHITELIST"], 
          DOWNLOADS_PATH=config["DOWNLOADS_PATH"]):
    
    file_id = 0
    file_page_path_url_table = []
    
    if BLACKLIST is None:
        BLACKLIST = []
    if WHITELIST is None:
        WHITELIST = []
        
    visited = set()
    queue = [] 

    # Helper to check if a URL should be crawled
    def is_valid_link(link):
        if not link or link in visited:
            return False

        parsed = urlparse(link)
        full_url = link if parsed.scheme else urljoin(base_url, link)
        
        # Always allow the starting URL, we start crawling from here
        if full_url == config["START_URL"]:
            return True
        
        if WHITELIST:
            if not any(full_url.startswith(allowed) for allowed in WHITELIST):
                return False

        if parsed.netloc and parsed.netloc not in start_netloc:
            return False

        if full_url.startswith("mailto:") or full_url.startswith("javascript:") or full_url.startswith("#"):
            return False

        if re.search(r"\.(pdf|jpg|jpeg|png|gif|bmp|zip|exe|doc|docx|xls|xlsx|ppt|pptx)$", full_url, re.IGNORECASE):
            return False

        for b_url in BLACKLIST:
            if full_url.startswith(b_url):
                return False

        return True

    # Prepare base domain info for internal link checking
    parsed_start = urlparse(START_URL) 
    start_netloc = {parsed_start.netloc}  
    base_url = parsed_start.scheme + "://" + parsed_start.netloc + parsed_start.path
    
    # Ensure base_url ends with '/' for proper urljoin with relative links
    if not base_url.endswith("/"):
        base_url = base_url.rsplit("/", 1)[0] + "/"

    def crawl_bfs(url):
        nonlocal file_id
        
        # Enqueue the URL with depth 0
        queue.append((url, 0))
        
        while queue:
            current_url, curr_depth = queue.pop(0)
            
            # Skip if max depth reached or URL already visited
            if curr_depth > MAX_DEPTH or current_url in visited:
                continue
            
            total = len(queue) + len(visited)
            print(f"{len(visited)}/{total} | Scraping: \"{current_url}\"...")
            
            # Try to fetch the page content
            try:
                response = requests.get(current_url)
            except Exception as e:
                continue
            
            content_type = response.headers.get("Content-Type", "")
            
            # Skip if not HTML content
            if "text/html" not in content_type:
                continue
            
            # Mark URL as visited
            visited.add(current_url)
            
            # Save the page content to a file
            html_content = response.text
            
            # Save 
            file_name, page_name = clean_and_save(current_url, html_content, DOWNLOADS_PATH)
            path = f"{DOWNLOADS_PATH}/{file_name}"
            file_page_path_url_table.append([file_name, page_name, path, current_url])
            file_id += 1
            
            # Parse and enqueue links
            soup = BeautifulSoup(html_content, "html.parser")
            for a in soup.find_all('a', href=True):
                link = a['href']
                full_link = link if urlparse(link).scheme else urljoin(current_url, link)
                
                # Check if valid link and is not already in the queue
                if (is_valid_link(full_link)) and (full_link not in (item[0] for item in queue)) and (full_link.startswith(base_url)):
                    queue.append((full_link, curr_depth + 1))
                    
            # Sleep after each page to avoid hammering the server
            time.sleep(random.uniform(0.5,1))

    crawl_bfs(START_URL)
    save_csv_index(file_page_path_url_table, DOWNLOADS_PATH)


def main():
    print("Starting web crawler...")
    crawl()   

    
if __name__ == "__main__":
    main()