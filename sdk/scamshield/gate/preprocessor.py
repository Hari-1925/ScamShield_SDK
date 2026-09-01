import re

class PreProcessor:
    @staticmethod
    def deobfuscate(text: str) -> str:
        """
        Reverses common leet-speak obfuscation tricks scammers use to bypass filters.
        """
        text = text.lower()
        
        # Leet speak replacements
        replacements = {
            '@': 'a',
            '4': 'a',
            '0': 'o',
            '1': 'i',
            '!': 'i',
            '3': 'e',
            '5': 's',
            '$': 's'
        }
        
        for k, v in replacements.items():
            text = text.replace(k, v)
            
        # Remove interspersed spaces/dots in words (e.g. "o t p", "o.t.p")
        # A simple heuristic: if there's a sequence of single characters separated by spaces/dots
        # This regex looks for patterns like 'o t p' or 'a c c o u n t'
        text = re.sub(r'(?:(?<=\s)|(?<=^))([a-z])(?:[\s\.]+([a-z]))+(?=\s|$)', lambda m: m.group(0).replace(' ', '').replace('.', ''), text)
        
        # Remove extra non-alphanumeric noise (but keep basic punctuation)
        text = re.sub(r'[^a-z0-9\s\.\,\?\!]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def extract_entities(text: str) -> dict:
        """
        Extracts URLs, Phone numbers, and UPI IDs for fast-path blocking.
        """
        url_regex = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        upi_regex = r'[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}'
        phone_regex = r'\+?\d{1,3}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        return {
            "urls": re.findall(url_regex, text),
            "upi_ids": re.findall(upi_regex, text),
            "phones": re.findall(phone_regex, text)
        }
