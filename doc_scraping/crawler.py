import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import re
import os

config = {
    "start_url": "https://www.opendental.com/site/apispecification.html",
    "max_depth": 2,
    "blacklist": [],
    "whitelist": ["https://www.opendental.com/site/api"],
    "output_dir": "./pages" ,
}

def clean_and_save(url, content, output_dir):
    soup = BeautifulSoup(content, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Remove navigation elements like nav and aside
    for tag in soup.find_all(["nav", "aside"]):
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
            # Remove the link and any separating characters around it
            link_parent = link.parent
            link.decompose()
            # If the parent is now empty or just punctuation, remove it as well
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
        
        if line in ("Open Dental Home", "Search"):
            continue
        if re.match(r"Manual v\d+\.\d", line):
            continue
        
        cleaned_lines.append(line)
        
    # Join lines, ensuring readable spacing
    cleaned_text = "\n".join(cleaned_lines)
    
    # Collapse multiple blank lines to one
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

    # Save the cleaned text to a file
    page_name = url.split("/")[-1].split(".")[0]
    file_name = f"{page_name}"
    output_path = os.path.join(output_dir, file_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

def save_html(url, html_content, output_dir):
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Extract the page name from the URL
    page_name = url.split("/")[-1].split(".")[0]
    
    # Save the HTML content to a text file
    with open(f"{output_dir}/{page_name}.html", "w") as f:
        f.write(html_content)

def crawl(start_url, max_depth=10, blacklist=None, whitelist=None, output_dir="./pages"):
    file_id = 0
    if blacklist is None:
        blacklist = []
    if whitelist is None:
        whitelist = []
        
    visited = set()
    queue = [] 

    # Helper to check if a URL should be crawled
    def is_valid_link(link):
        if not link or link in visited:
            return False

        parsed = urlparse(link)
        full_url = link if parsed.scheme else urljoin(base_url, link)
        
        # Always allow the starting URL
        if full_url == config["start_url"]:
            return True
        
        # Enforce whitelist: the full URL must start with one of the allowed entries
        if whitelist:
            if not any(full_url.startswith(allowed) for allowed in whitelist):
                return False

        # (Other checks remain unchanged)
        if parsed.netloc and parsed.netloc not in start_netloc:
            return False

        if full_url.startswith("mailto:") or full_url.startswith("javascript:") or full_url.startswith("#"):
            return False

        if re.search(r"\.(pdf|jpg|jpeg|png|gif|bmp|zip|exe|doc|docx|xls|xlsx|ppt|pptx)$", full_url, re.IGNORECASE):
            return False

        # Check against blacklist
        for b_url in blacklist:
            if full_url.startswith(b_url):
                return False

        return True

    # Prepare base domain info for internal link checking
    parsed_start = urlparse(start_url) 
    start_netloc = {parsed_start.netloc}  # allowed domains (could include subdomains if needed)
    base_url = parsed_start.scheme + "://" + parsed_start.netloc + parsed_start.path
    
    # Ensure base_url ends with '/' for proper urljoin with relative links
    if not base_url.endswith("/"):
        base_url = base_url.rsplit("/", 1)[0] + "/"
    base_path = os.path.dirname(parsed_start.path)  # e.g., "/manual243"

    def crawl_bfs(url):
        nonlocal file_id
        
        # BFS using a queue
        queue.append((url, 0)) # (url, depth)
        
        while queue:
            current_url, depth = queue.pop(0)
            
            # Skip if max depth reached or URL already visited
            if depth > max_depth or current_url in visited:
                continue
            
            print(f"Queue size: {len(queue)}, Visited: {len(visited)}")
            print(f"Current URL: {current_url}")
            
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
            
            # Save the HTML content to a file
            # save_html(current_url, html_content, output_dir)
            clean_and_save(current_url, html_content, output_dir)
            file_id += 1
            
            # Parse and enqueue links
            soup = BeautifulSoup(html_content, "html.parser")
            
            for a in soup.find_all('a', href=True):
                link = a['href']
                full_link = link if urlparse(link).scheme else urljoin(current_url, link)
                if is_valid_link(full_link):
                    queue.append((full_link, depth + 1))
                    
            # Sleep after each page to avoid hammering the server
            time.sleep(random.uniform(0.5,1))

    # Start the crawl
    crawl_bfs(start_url)

if __name__ == "__main__":
    crawl(config["start_url"], config["max_depth"], config["blacklist"], config["whitelist"], config["output_dir"])