import pickle
from pdfminer.high_level import extract_text
import networkx as nx
from collections import defaultdict
import re
import os

PDF_PATH = "C:/Users/milan/OneDrive/Desktop/SIIT/2. Semestar/Algoritmi i Strukture/Projekat 2/Data Structures and Algorithms in Python.pdf"
OFFSET = 22  # Offset za prve 22 nenumerisane stranice
SERIALIZED_GRAPH_PATH = 'graph.pickle'
SERIALIZED_TRIE_PATH = 'trie.pickle'
SERIALIZED_TEXT_PATH = 'text.pickle'


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def starts_with(self, prefix):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return True

def save_object(obj, file_name):
    with open(file_name, 'wb') as f:
        pickle.dump(obj, f)

def load_object(file_name):
    with open(file_name, 'rb') as f:
        return pickle.load(f)

def extract_text_from_pdf(pdf_path):
    text = extract_text(pdf_path)
    pages = text.split('\x0c')  # Split the text into pages
    return pages

def initialize_trie(text):
    trie = Trie()
    for page in text:
        words = re.findall(r'\w+', page)
        for word in words:
            trie.insert(word)
    return trie

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

def search_keywords(text, keywords, G, trie):
    results = defaultdict(list)
    keyword_count = defaultdict(int)
    page_order = []

    for page_num, page in enumerate(text):
        lines = page.split('\n')
        keyword_found = False
        found_keywords = set()

        for line_num, line in enumerate(lines):
            for keyword in keywords:
                if trie.search(keyword):
                    if re.search(keyword, line, re.IGNORECASE):
                        context_highlighted = re.sub(keyword, lambda x: f"\033[91m{x.group()}\033[0m", line, flags=re.IGNORECASE)
                        results[page_num + 1].append((line_num + 1, context_highlighted))
                        keyword_count[page_num + 1] += len(re.findall(keyword, line, re.IGNORECASE))
                        found_keywords.add(keyword)
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

def display_results(results, keyword_count, page_order, G, keywords, text, results_per_page=20):
    total_ranks = {}
    for page_num in results:
        in_edges = G.in_edges(page_num, data=True)
        keyword_count_on_page = sum(len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for keyword in keywords)
        num_keywords = sum(1 for keyword in keywords if re.search(keyword, text[page_num - 1], re.IGNORECASE))
        link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
        referring_keywords_bonus = sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) * 7
                                       for source, _, data in in_edges for keyword in keywords if re.search(keyword, text[source - 1], re.IGNORECASE))
        total_ranks[page_num] = keyword_count_on_page + num_keywords * 5 + link_bonus + referring_keywords_bonus

    ranked_results = sorted(total_ranks.items(), key=lambda x: x[1], reverse=True)
    total_pages = len(ranked_results)
    current_page = 0

    while True:
        start_index = current_page * results_per_page
        end_index = start_index + results_per_page
        for page_num, _ in ranked_results[start_index:end_index]:
            search_result = page_order.index(page_num) + 1
            in_edges = G.in_edges(page_num, data=True)

            # Reinitialize values for each page displayed
            keyword_count_on_page = sum(len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for keyword in keywords)
            num_keywords = sum(1 for keyword in keywords if re.search(keyword, text[page_num - 1], re.IGNORECASE))
            link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
            referring_keywords_bonus = sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) * 7
                                           for source, _, data in in_edges for keyword in keywords if re.search(keyword, text[source - 1], re.IGNORECASE))

            print(f"\nSearch Result: {search_result}, Page: {page_num}, Rank: {total_ranks[page_num]}")
            matches = results.get(page_num, [])  # Ensure to get matches or an empty list if no matches
            for line_num, context in matches:
                print(f"{line_num}. {context}")
            if in_edges:
                link_info = ', '.join(f"Page {source} ({data['weight']} times)" for source, _, data in in_edges)
                print(f"Linked from pages: {link_info}")
                keyword_details = {source: sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) for keyword in keywords) for source, _, _ in in_edges}
                for source, count in keyword_details.items():
                    print(f"Keywords on Page {source}: {count} times")

            print(f"Formula for rank: {keyword_count_on_page} (appearances) + {num_keywords} (distinct keywords) * 5 + {link_bonus} (links bonus) + {referring_keywords_bonus} (referring keywords bonus) = {total_ranks[page_num]}")

        if end_index >= total_pages:
            print("\nEnd of results.")
            break
        else:
            response = input(f"\nDisplayed {end_index} of {total_pages} results. Enter 'next' for next {results_per_page} results, 'all' for all results, or 'done' to finish: ")
            if response.lower() == 'next':
                current_page += 1
            elif response.lower() == 'all':
               # Display all results
                print("\nEnd of results.")
                break
            elif response.lower() == 'done':
                break
def search_menu():
    if os.path.exists(SERIALIZED_GRAPH_PATH) and os.path.exists(SERIALIZED_TRIE_PATH) and os.path.exists(SERIALIZED_TEXT_PATH):
        G = load_object(SERIALIZED_GRAPH_PATH)
        trie = load_object(SERIALIZED_TRIE_PATH)
        text = load_object(SERIALIZED_TEXT_PATH)
    else:
        text = extract_text_from_pdf(PDF_PATH)
        G = initialize_graph(text)
        trie = initialize_trie(text)
        save_object(G, SERIALIZED_GRAPH_PATH)
        save_object(trie, SERIALIZED_TRIE_PATH)
        save_object(text, SERIALIZED_TEXT_PATH)

    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        keywords = query.split()
        results, keyword_count, page_order = search_keywords(text, keywords, G, trie)
        display_results(results, keyword_count, page_order, G, keywords, text)


if __name__ == "__main__":
    search_menu()
