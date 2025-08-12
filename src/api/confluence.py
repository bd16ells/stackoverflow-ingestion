# This code sample uses the 'requests' library:
# http://docs.python-requests.org
from typing import List
import requests
from requests.auth import HTTPBasicAuth
import os
from bs4 import BeautifulSoup, NavigableString

class ConfluenceAPI:

    def __init__(self, api_url, api_token, cert_path: str = None, output_dir = "tmp/confluence"):
        """
        Initialize the StackOverflow API client.
        
        :param api_url: Base URL for the StackOverflow API
        :param api_token: API token for authentication
        """
        self.api_url = api_url
        self.api_token = api_token
        self.headers = {"Accept": "application/json", 
                        "Authorization": f"Bearer {self.api_token}"}
        self.cert_path = cert_path
        self.output_dir = output_dir


    def get_page_content(self, page_id):
        url = f"{self.api_url}/rest/api/content/{page_id}?expand=body.storage"
        response = requests.get(url, headers=self.headers, verify=self.cert_path)
        if response.status_code == 200:
            return response.json().get("body", {}).get("storage", {}).get("value", "")
        else:
            print(f"Failed to fetch content for page {page_id}: {response.status_code}")
            return ""

    def convert_list_to_markdown(self, tag, indent_level=0):
        markdown = ""
        indent = "  " * indent_level
        if tag.name == "ul":
            for li in tag.find_all("li", recursive=False):
                item = self.convert_children_to_markdown(li, indent_level + 1).strip()
                markdown += f"{indent}- {item}\n"
        elif tag.name == "ol":
            for i, li in enumerate(tag.find_all("li", recursive=False), start=1):
                item = self.convert_children_to_markdown(li, indent_level + 1).strip()
                markdown += f"{indent}{i}. {item}\n"
        return markdown

    def convert_table_to_markdown(self, table):
        rows = table.find_all("tr")
        markdown = ""
        for i, row in enumerate(rows):
            cols = row.find_all(["td", "th"])
            line = "| " + " | ".join(col.get_text(strip=True) for col in cols) + " |\n"
            markdown += line
            if i == 0:
                markdown += "| " + " | ".join("---" for _ in cols) + " |\n"
        return markdown

    def convert_children_to_markdown(self, tag, indent_level=0):
        markdown = ""
        for child in tag.children:
            if isinstance(child, NavigableString):
                markdown += str(child)
            elif child.name in ["ul", "ol"]:
                markdown += "\n" + self.convert_list_to_markdown(child, indent_level)
            elif child.name == "a":
                href = child.get("href", "")
                text = child.get_text()
                markdown += f"{text}"
            elif child.name == "strong":
                markdown += f"**{self.convert_children_to_markdown(child, indent_level)}**"
            elif child.name == "em":
                markdown += f"*{self.convert_children_to_markdown(child, indent_level)}*"
            elif child.name == "br":
                markdown += "\n"
            elif child.name == "table":
                markdown += "\n" + self.convert_table_to_markdown(child) + "\n"
            else:
                markdown += self.convert_children_to_markdown(child, indent_level)
        return markdown

    def html_to_markdown(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        markdown = ""

        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table"], recursive=False):
            if element.name.startswith("h"):
                level = int(element.name[1])
                markdown += "#" * level + " " + element.get_text(strip=True) + "\n\n"
            elif element.name == "p":
                markdown += self.convert_children_to_markdown(element).strip() + "\n\n"
            elif element.name in ["ul", "ol"]:
                markdown += self.convert_list_to_markdown(element) + "\n"
            elif element.name == "table":
                markdown += self.convert_table_to_markdown(element) + "\n"

        return markdown

    def get_child_pages(self, page_id):
        url = f"{self.api_url}/rest/api/content/{page_id}/child/page"
        response = requests.get(url, headers=self.headers, verify=self.cert_path)
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            print(f"Failed to fetch children for page {page_id}: {response.status_code}")
            return []

    def save_all_descendants(self, page_id, classifier):
        children = self.get_child_pages(page_id)
        for child in children:
            title = child.get("title", "Untitled")
            child_id = child.get("id")
            content_html = self.get_page_content(child_id)
            content_md = self.html_to_markdown(content_html)

            filename = title.replace(" ", "_").replace("/", "and") + ".md"
            abs_path = f"{self.output_dir}/{classifier}"
            os.makedirs(abs_path, exist_ok=True)
            with open(f"{abs_path}/{filename}", "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(content_md)

            print(f"✅ Saved: {filename}")
            self.save_all_descendants(child_id, classifier)

    def do_process(self, page, classifier):
        print(f"Processing starting page: {page} with classification: {classifier}")
        self.save_all_descendants(page, classifier)
    
    def process_single_page(self, page_id, classifier):
        """
        Process a single Confluence page and save its content.
        
        :param page_id: ID of the Confluence page to process
        :param classifier: Classifier for the output directory
        """
        content_html = self.get_page_content(page_id)
        content_md = self.html_to_markdown(content_html)

        title = classifier
        filename = title.replace(" ", "_").replace("/", "and") + ".md"
        abs_path = f"{self.output_dir}/{classifier}"
        os.makedirs(abs_path, exist_ok=True)
        with open(f"{abs_path}/{filename}", "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(content_md)

        print(f"✅ Saved: {filename}")
