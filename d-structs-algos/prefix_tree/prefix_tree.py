class PrefixTree:
    def __init__(self):
        self.root = {}
        self.end_symbol = "*"
    
    def insert(self, word):
        current = self.root
        for c in word:
            if c not in current:
                current[c] = {}
            current = current[c]
        current[self.end_symbol] = True
    
    def exists(self, word):
        current = self.root
        for letter in word:
            if letter not in current:
                return False
            current = current[letter]
        return '*' in current
    
    def search_level(self, current_level, current_prefix, words):
        if self.end_symbol in current_level:
            words.append(current_prefix)
        for letter, next_level in current_level.items():
            if letter != self.end_symbol:
                self.search_level(next_level, current_prefix + letter, words)
                
    def words_with_prefix(self, prefix):
        current = self.root
        for letter in prefix:
            if letter not in current:
                return []
            current = current[letter]
        words = []
        self.search_level(current, prefix, words)
        return words
    
    def find_matches(self, document):
        matches = set()
        for i in range (0, len(document)):
            current_level = self.root
            for j in range(i, len(document)):
                if document[j] not in current_level:
                    break
                current_level = current_level[document[j]]
                if self.end_symbol in current_level:
                    matches.add(document[i:j+1])
        return matches
    
    def advanced_find_matches(self, document, variations):
        matches = set()
        for i in range(len(document)):
            current_level = self.root
            for j in range(i, len(document)):
                canonical = variations.get(document[j], document[j])
                if canonical not in current_level:
                    break
                current_level = current_level[canonical]
                if self.end_symbol in current_level:
                    matches.add(document[i:j+1])
        return matches
    
    
    def longest_common_prefix(self):
        prefix = ""
        current = self.root
        while len(current) == 1 and self.end_symbol not in current:
            letter = next(iter(current))
            prefix += letter
            current = current[letter]
        return prefix
    
   