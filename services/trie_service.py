from typing import List, Dict, Any

class TrieNode:
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.songs: List[Dict[str, Any]] = []

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, title: str, song: dict):
        node = self.root
        title_lower = title.lower()
        
        for char in title_lower:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end = True
        node.songs.append(song)
    
    def search_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        node = self.root
        
        prefix_lower = prefix.lower()
        for char in prefix_lower:
            if char not in node.children:
                return []
            node = node.children[char]
        
        return self._collect_songs(node)
    
    def _collect_songs(self, node: TrieNode) -> List[Dict[str, Any]]:
        results = node.songs[:]
        for child in node.children.values():
            results.extend(self._collect_songs(child))
        return results
    
    def build_from_playlist(self, songs: List[Dict[str, Any]]):
        self.root = TrieNode()
        for song in songs:
            self.insert(song["title"], song)

def create_trie_for_playlist(songs: List[Dict[str, Any]]) -> Trie:
    trie = Trie()
    trie.build_from_playlist(songs)
    return trie
