from abc import ABC, abstractmethod
from typing import Dict, Any


class Parser(ABC):
    @abstractmethod
    def to_clean_json(self) -> Dict[str, Any]:
        pass

    def parse_to_outfile(self, outfile: str) -> None:
        """
        Write the parsed data to a JSON file.
        
        :param outfile: Path to the output file
        """
        import json
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(self.to_clean_json(), f, ensure_ascii=False, indent=4)