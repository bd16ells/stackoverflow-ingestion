from typing import Dict, Any, List
from bs4 import BeautifulSoup, NavigableString
import html
from util.Parser.parser import Parser


class QuestionParser(Parser):
    def __init__(self, response_data: Dict[str, Any]):
        self.response_data = response_data
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

    def parse_body_to_markdown(self, raw_html: str) -> str:
        soup = BeautifulSoup(html.unescape(raw_html), 'html.parser')

        
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
                content = [process_element(child, indent + 1) for child in el.contents]
                return f"{'  ' * indent}- {' '.join(filter(None, content)).strip()}"
            elif el.name in ['ul', 'ol']:
                items = [process_element(li, indent) for li in el.find_all('li', recursive=False)]
                return '\n'.join(items)
            elif el.name == 'pre':
                # Check if <code> is inside <pre>
                code_block = el.find('code')
                if code_block:
                    return f"```\n{code_block.get_text()}\n```"
                else:
                    return f"```\n{el.get_text()}\n```"
            elif el.name == 'code':
                # Inline code
                return f"`{self.format_inline(el)}`"
            elif el.name == 'blockquote':
                return '> ' + self.format_inline(el)
            return ''


        markdown_lines = []
        for child in soup.contents:
            if hasattr(child, 'name'):
                line = process_element(child)
                if line:
                    markdown_lines.append(line)

        return '\n\n'.join(markdown_lines)

    def to_clean_json(self) -> List[Dict[str, Any]]:
        question = {
            "title": self.response_data.get("title"),
            "tags": self.response_data.get("tags", []),
            "author": self.response_data.get("owner", {}).get("display_name"),
            "score": self.response_data.get("score"),
            "created": self.response_data.get("creation_date"),
            "link": self.response_data.get("link"),
            "body_markdown": self.parse_body_to_markdown(self.response_data.get("body", "")),
            "answers": []
        }

        for answer in self.response_data.get("answers", []):
            parsed_answer = {
                "author": answer.get("owner", {}).get("display_name"),
                "score": answer.get("score"),
                "created": answer.get("creation_date"),
                "is_accepted": answer.get("is_accepted"),
                "body_markdown": self.parse_body_to_markdown(answer.get("body", ""))
            }
            question["answers"].append(parsed_answer)

        return question
