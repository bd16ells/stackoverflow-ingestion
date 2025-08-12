from abc import ABC, abstractmethod
from typing import Dict, Any
from bs4 import BeautifulSoup, NavigableString
import html
from util.Parser.parser import Parser


class ArticleParser(Parser):
    def __init__(self, article_data: Dict[str, Any]):
        self.article_data = article_data
        self.raw_html = html.unescape(article_data.get("body", ""))
        self.soup = BeautifulSoup(self.raw_html, 'html.parser')


    
    def format_inline(self, el) -> str:
        if isinstance(el, NavigableString):
            return el.strip()
        elif el.name == 'strong':
            return f"**{''.join(self.format_inline(c) for c in el.contents)}**"
        elif el.name == 'em':
            return f"_{''.join(self.format_inline(c) for c in el.contents)}_"
        elif el.name == 'code':
            return f"`{''.join(self.format_inline(c) for c in el.contents)}`"
        elif el.name == 'a':
            href = el.get('href', '').strip()
            text = ''.join(self.format_inline(c) for c in el.contents).strip()
            return f"{text} [{href}]" if href else text
        else:
            return ''.join(self.format_inline(c) for c in el.contents)



        
    def parse_body_to_markdown(self) -> str:
        def process_element(el, indent=0):
            if isinstance(el, NavigableString):
                return el.strip()

            if el.name == 'h1':
                return f"# {self.format_inline(el)}"
            elif el.name == 'h2':
                return f"## {self.format_inline(el)}"
            elif el.name == 'h3':
                return f"### {self.format_inline(el)}"
            elif el.name == 'p':
                return self.format_inline(el)
            elif el.name == 'li':
                content = []
                for child in el.contents:
                    content.append(process_element(child, indent + 1))
                return f"{'  ' * indent}- {' '.join(filter(None, content)).strip()}"
            elif el.name in ['ul', 'ol']:
                items = []
                for li in el.find_all('li', recursive=False):
                    items.append(process_element(li, indent))
                return '\n'.join(items)
            elif el.name == 'pre':
                return "```\n" + el.get_text() + "\n```"
            elif el.name == 'blockquote':
                return '> ' + self.format_inline(el)
            return ''

        markdown_lines = []
        for child in self.soup.contents:
            print(child)
            if hasattr(child, 'name'):
                line = process_element(child)
                if line:
                    markdown_lines.append(line)

        return '\n\n'.join(markdown_lines)


    def to_clean_json(self) -> Dict[str, Any]:
        return {
            "title": self.article_data.get("title"),
            "tags": self.article_data.get("tags", []),
            "author": self.article_data.get("owner", {}).get("display_name"),
            "score": self.article_data.get("score"),
            "created": self.article_data.get("creation_date"),
            "link": self.article_data.get("link"),
            "body_markdown": self.parse_body_to_markdown()
        }
