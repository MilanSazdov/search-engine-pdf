from pdfminer.high_level import extract_text
import networkx as nx
from collections import defaultdict
import re

PDF_PATH = "C:/Users/milan/OneDrive/Desktop/SIIT/2. Semestar/Algoritmi i Strukture/Projekat 2/Data Structures and Algorithms in Python.pdf"
OFFSET = 22  # Offset za prve 22 nenumerisane stranice

def extract_text_from_pdf(pdf_path):
    text = extract_text(pdf_path)
    pages = text.split('\x0c')  # Split the text into pages
    return pages

def initialize_graph(text):
    G = nx.DiGraph()
    link_patterns = [
        r'see page (\d+)', r'refer to page (\d+)', r'turn to page (\d+)', r'check page (\d+)', r'on page (\d+)',
        r'consult page (\d+)', r'found on page (\d+)', r'look at page (\d+)', r'continued on page (\d+)',
        r'more on page (\d+)', r'details on page (\d+)', r'see also page (\d+)', r'refer back to page (\d+)',
        r'refer ahead to page (\d+)', r'go to page (\d+)', r'information on page (\d+)', r'see further on page (\d+)',
        r'continued from page (\d+)', r'further details on page (\d+)', r'refer to the section on page (\d+)',
        r'from page (\d+)', r'\(page (\d+)\)', r'from pages (\d+)', r'\(pages (\d+)\)'
    ]
    link_pattern = re.compile('|'.join(link_patterns), re.IGNORECASE)

    for page_num, page in enumerate(text):
        G.add_node(page_num + 1)  # Add each page as a node
        lines = page.split('\n')
        for line in lines:
            for match in link_pattern.finditer(line):
                for i in range(1, len(match.groups()) + 1):
                    if match.group(i):
                        linked_page = int(match.group(i)) + OFFSET
                        if G.has_edge(page_num + 1, linked_page):
                            # Increase the weight if the edge already exists
                            G[page_num + 1][linked_page]['weight'] += 1
                        else:
                            # Create a new edge with weight 1 if it does not exist
                            G.add_edge(page_num + 1, linked_page, weight=1)

    return G

class TrieNode:
    def __init__(self):
        self.children = {}
        self.end_of_word = False  # Indicates the end of a word

def add_word(root, word):
    node = root
    for char in word.lower():  # Convert to lowercase to ensure case-insensitivity
        if char not in node.children:
            node.children[char] = TrieNode()
        node = node.children[char]
    node.end_of_word = True

def search_word(root, word):
    # Search for any substring of 'word' starting from any node in the Trie
    for start in range(len(word)):
        node = root
        for char in word[start:].lower():
            if char not in node.children:
                break
            node = node.children[char]
            if node.end_of_word:
                return True
    return False


def initialize_trie(keywords):
    root = TrieNode()
    for keyword in keywords:
        add_word(root, keyword)
    return root

def search_keywords(text, keywords, G):
    trie_root = initialize_trie(keywords)
    results = defaultdict(list)
    keyword_count = defaultdict(int)
    page_order = []

    for page_num, page in enumerate(text):
        lines = page.split('\n')
        keyword_found = False
        found_keywords = set()

        for line_num, line in enumerate(lines):
            words = line.split()
            for word in words:
                if search_word(trie_root, word):
                    found_keywords.add(word)
                    context_highlighted = re.sub(word, lambda x: f"\033[91m{x.group()}\033[0m", line, flags=re.IGNORECASE)
                    results[page_num + 1].append((line_num + 1, context_highlighted))
                    keyword_count[page_num + 1] += 1
                    if not keyword_found:
                        page_order.append(page_num + 1)
                        keyword_found = True

        # Bonus points for pages containing multiple keywords
        keyword_count[page_num + 1] += len(found_keywords) * 5

    # Adding points based on links to pages
    for page in G.nodes:
        in_edges = G.in_edges(page, data=True)
        link_bonus = sum(data.get('weight', 1) * 10 for _, _, data in in_edges)
        keyword_count[page] += link_bonus

    return results, keyword_count, page_order


def display_results(results, keyword_count, page_order, G, keywords, text):
    total_ranks = {}
    for page_num in results:
        in_edges = G.in_edges(page_num, data=True)
        keyword_count_on_page = sum(len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for keyword in keywords)
        num_keywords = sum(1 for keyword in keywords if re.search(keyword, text[page_num - 1], re.IGNORECASE))
        link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
        referring_keywords_bonus = sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) * 7
                                       for source, _, data in in_edges for keyword in keywords if re.search(keyword, text[source - 1], re.IGNORECASE))
        total_ranks[page_num] = keyword_count_on_page + num_keywords * 5 + link_bonus + referring_keywords_bonus

    ranked_results = sorted(results.items(), key=lambda x: total_ranks[x[0]], reverse=True)

    for page_num, matches in ranked_results:
        search_result = page_order.index(page_num) + 1
        in_edges = G.in_edges(page_num, data=True) # Refresh in_edges for each page

        # Recalculate values for the current page
        keyword_count_on_page = sum(len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for keyword in keywords)
        num_keywords = sum(1 for keyword in keywords if re.search(keyword, text[page_num - 1], re.IGNORECASE))
        link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
        referring_keywords_bonus = sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) * 7
                                       for source, _, data in in_edges for keyword in keywords if re.search(keyword, text[source - 1], re.IGNORECASE))

        print(f"Search Result: {search_result}, Page: {page_num}, Rank: {total_ranks[page_num]}")
        for line_num, context in matches:
            print(f"{line_num}. {context}")

        if in_edges:
            link_info = ', '.join(f"Page {source} ({data['weight']} times)" for source, _, data in in_edges)
            print(f"Linked from pages: {link_info}")
            # Update keyword details count
            keyword_details = defaultdict(int)
            for source, _, data in in_edges:
                for keyword in keywords:
                    keyword_count = len(re.findall(keyword, text[source - 1], re.IGNORECASE))
                    keyword_details[source] += keyword_count
            for source, count in keyword_details.items():
                print(f"Keywords on Page {source}: {count} times")

        print(
            f"Formula for rank: {keyword_count_on_page} (appearances) + {num_keywords} (distinct keywords) * 5 + {link_bonus} (links bonus) + {referring_keywords_bonus} (referring keywords bonus) = {total_ranks[page_num]}")
        print()


def search_menu():
    text = extract_text_from_pdf(PDF_PATH)
    G = initialize_graph(text)
    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        keywords = query.split()
        results, keyword_count, page_order = search_keywords(text, keywords, G)
        display_results(results, keyword_count, page_order, G, keywords, text)

if __name__ == "__main__":
    search_menu()