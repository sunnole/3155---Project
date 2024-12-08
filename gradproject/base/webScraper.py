# import requests
from bs4 import BeautifulSoup
import pandas as pd
# from tenacity import retry, wait_exponential, stop_after_attempt
from fake_useragent import UserAgent
# import aiohttp
# import asyncio
import httpx

# Headers to mitigate anti-bot measures
ua = UserAgent()
HEADERS = {
    "User-Agent": ua.random
}

# async def fetch_page_async(url):
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url)
#             response.raise_for_status() # Raise an error for non-200 status codes
#             return response.text
#         # async with aiohttp.ClientSession() as session:
#         #     async with session.get(url, headers=HEADERS, timeout=10) as response:
#         #         return await response.text()

# Sync fetch page
def fetch_page(url):
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text

# Extract Grad program name
def extract_name(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else None
    h1 = soup.find("h1").text.strip() if soup.find("h1") else None
    program_name = title or h1 or  "program"
    sanitized_name = "".join(c for c in program_name if c.isalnum() or c in (' ', '-')).strip()
    return sanitized_name


# Parse HTML content using BeautifulSoup
def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    data = []

    # Parse only from div.page
    page_div = soup.find("div", {"class": "page"})

    # Extract sections and assign to variables
    if page_div:
        # Extract relevant content (headings, paragraphs, lists, etc.) from this div
        for section in page_div.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
            tag_type = section.name  # HTML tag type (e.g., h1, p)
            content = section.text.strip()  # Content of the tag
            links = [a["href"] for a in section.find_all("a", href=True)]  # Extract links if present

            # Filter out content from irrelevant sections (e.g., navigation or footer)
            if content and not section.find_parent(['nav', 'footer']):
                data.append({
                    "tag": tag_type,
                    "content": content,
                    "links": links
                })

    return data


# Organize data for page template exportation & application
def organize_data(data):
    organized_data = {}

    current_header = None
    for item in data:
        tag = item["tag"]
        content = item["content"]
        links = item["links"]

        # Group by tags
        if tag.startswith("h"):
            current_header = content
            organized_data[current_header] = {"paragraphs": [], "links": links}
        elif tag == "p":
            if current_header:
                organized_data[current_header]["paragraphs"].append(content)
        elif tag in ["ul", "ol"]:
            if current_header:
                organized_data[current_header]["list"] = content.split("\n")

    return organized_data

# Save to Files
def save_to_files(data, cvs_file, json_file):
    # Save to both JSON and CSV for redundancy
    df=pd.DataFrame(data)
    df.to_csv(cvs_file, index=False)

    with open(json_file, 'w', encoding="utf-8") as f:
        pd.DataFrame(data).to_json(f, orient="records", indent=4)

# Save to database


# Check for robots.txt for instructions
# def check_robots_txt(url):
#     base_url = "/".join(url.split("/")[:3])
#     robots_url = f"{base_url}/robots.txt"
#
#     try:
#         response = requests.get(robots_url, headers=HEADERS, timeout=5)
#         if response.status_code == 200:
#             print("robots.txt found. Please ensure compliance!")
#             print(response.text)
#     except requests.exceptions.RequestException as e:
#         print("Could not fetch robots.txt:", e)