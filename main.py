import pickle
from pdfminer.high_level import extract_text
import networkx as nx
from collections import defaultdict
import re
import os
from difflib import get_close_matches
from PyPDF2 import PdfReader, PdfWriter

PDF_PATH = "C:/Users/milan/OneDrive/Desktop/SIIT/2. Semestar/Algoritmi i Strukture/Projekat 2/Data Structures and Algorithms in Python.pdf"
OFFSET = 22  # Offset za prve 22 nenumerisane stranice
SERIALIZED_GRAPH_PATH = 'graph.pickle'
SERIALIZED_TRIE_PATH = 'trie.pickle'
SERIALIZED_TEXT_PATH = 'text.pickle'
RESULT_PDF_PATH = 'search_results.pdf'

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

    def autocomplete(self, prefix):
        def dfs(node, prefix, results):
            if node.is_end_of_word:
                results.append(prefix)
            for char, child_node in node.children.items():
                dfs(child_node, prefix + char, results)

        results = []
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return results
            node = node.children[char]
        dfs(node, prefix, results)
        return results


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


def parse_query(query):
    """
    Parse the query to handle complex logical operators and phrases.
    """
    query = query.lower()
    tokens = re.split(r'(\band\b|\bor\b|\bnot\b)', query)
    parsed_query = []
    for token in tokens:
        if token in ('and', 'or', 'not'):
            parsed_query.append(token.upper())
        else:
            phrases = re.findall(r'"([^"]+)"', token)
            words = re.findall(r'\b\w+\b', re.sub(r'"[^"]+"', '', token))
            parsed_query.append(phrases + words)
    return parsed_query


def evaluate_query(parsed_query, trie, text):
    results = defaultdict(set)
    current_operator = 'OR'
    current_result_set = set()

    for token in parsed_query:
        if isinstance(token, list):  # This is a list of keywords/phrases
            temp_result_set = set()
            for page_num, page in enumerate(text):
                for keyword in token:
                    if keyword in page.lower():
                        temp_result_set.add(page_num + 1)
            if current_operator == 'AND':
                current_result_set &= temp_result_set
            elif current_operator == 'OR':
                current_result_set |= temp_result_set
            elif current_operator == 'NOT':
                current_result_set -= temp_result_set
        else:  # This is an operator
            current_operator = token

    return current_result_set


def search_keywords(text, parsed_query, G, trie):
    results = defaultdict(list)
    keyword_count = defaultdict(int)
    page_order = []

    matched_pages = evaluate_query(parsed_query, trie, text)

    for page_num in matched_pages:
        lines = text[page_num - 1].split('\n')
        for line_num, line in enumerate(lines):
            for token in parsed_query:
                if isinstance(token, list):  # This is a list of keywords/phrases
                    for keyword in token:
                        if keyword in line.lower():
                            context_highlighted = re.sub(keyword, lambda x: f"\033[91m{x.group()}\033[0m", line,
                                                         flags=re.IGNORECASE)
                            results[page_num].append((line_num + 1, context_highlighted))
                            keyword_count[page_num] += len(re.findall(keyword, line, re.IGNORECASE))
                            if page_num not in page_order:
                                page_order.append(page_num)
                            break

        # Bonus points for pages containing multiple keywords
        keyword_count[page_num] += len(
            set([keyword for token in parsed_query if isinstance(token, list) for keyword in token])) * 5

    # Adding points based on links to pages
    for page in G.nodes:
        in_edges = G.in_edges(page, data=True)
        link_bonus = sum(data.get('weight', 1) * 10 for _, _, data in in_edges)
        keyword_count[page] += link_bonus

    return results, keyword_count, page_order


def display_results(results, keyword_count, page_order, G, parsed_query, text, results_per_page=20):
    total_ranks = {}
    for page_num in results:
        in_edges = G.in_edges(page_num, data=True)
        keyword_count_on_page = sum(
            len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for token in parsed_query if
            isinstance(token, list) for keyword in token)
        num_keywords = sum(1 for token in parsed_query if isinstance(token, list) for keyword in token if
                           re.search(keyword, text[page_num - 1], re.IGNORECASE))
        link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
        referring_keywords_bonus = sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) * 7
                                       for source, _, data in in_edges for token in parsed_query if
                                       isinstance(token, list) for keyword in token if
                                       re.search(keyword, text[source - 1], re.IGNORECASE))
        total_ranks[page_num] = keyword_count_on_page + num_keywords * 5 + link_bonus + referring_keywords_bonus

    # Create a list of (page_num, rank) and sort by page number to assign search result indices
    sorted_by_page_number = sorted(total_ranks.items())
    search_result_indices = {page_num: index + 1 for index, (page_num, _) in enumerate(sorted_by_page_number)}

    # Sort by rank in descending order for display
    ranked_results = sorted(total_ranks.items(), key=lambda x: x[1], reverse=True)

    total_pages = len(ranked_results)
    current_page = 0

    save_pdf_pages([page_num for page_num, _ in ranked_results[:10]])

    while True:
        start_index = current_page * results_per_page
        end_index = start_index + results_per_page
        end_index = min(end_index, total_pages)  # Ensure we don't exceed the total results

        for page_index, (page_num, _) in enumerate(ranked_results[start_index:end_index], start=start_index + 1):
            in_edges = G.in_edges(page_num, data=True)

            # Reinitialize values for each page displayed
            keyword_count_on_page = sum(
                len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for token in parsed_query if
                isinstance(token, list) for keyword in token)
            num_keywords = sum(1 for token in parsed_query if isinstance(token, list) for keyword in token if
                               re.search(keyword, text[page_num - 1], re.IGNORECASE))
            link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
            referring_keywords_bonus = sum(len(re.findall(keyword, text[source - 1], re.IGNORECASE)) * 7
                                           for source, _, data in in_edges for token in parsed_query if
                                           isinstance(token, list) for keyword in token if
                                           re.search(keyword, text[source - 1], re.IGNORECASE))

            search_result = search_result_indices[page_num]  # Get the search result index based on page number

            print(f"\nSearch Result: {search_result}, Page: {page_num}, Rank: {total_ranks[page_num]}")
            matches = results.get(page_num, [])  # Ensure to get matches or an empty list if no matches
            for line_num, context in matches:
                print(f"{line_num}. {context}")
            if in_edges:
                link_info = ', '.join(f"Page {source} ({data['weight']} times)" for source, _, data in in_edges)
                print(f"Linked from pages: {link_info}")
                keyword_details = {source: sum(
                    len(re.findall(keyword, text[source - 1], re.IGNORECASE)) for token in parsed_query if
                    isinstance(token, list) for keyword in token) for source, _, _ in in_edges}
                for source, count in keyword_details.items():
                    print(f"Keywords on Page {source}: {count} times")

            print(
                f"Formula for rank: {keyword_count_on_page} (appearances) + {num_keywords} (distinct keywords) * 5 + {link_bonus} (links bonus) + {referring_keywords_bonus} (referring keywords bonus) = {total_ranks[page_num]}")

        if end_index >= total_pages:
            print("\nEnd of results.")
            break
        else:
            response = input(
                f"\nDisplayed {end_index} of {total_pages} results. Enter 'next' for next {results_per_page} results, 'all' for all results, or 'done' to finish: ")
            if response.lower() == 'next':
                current_page += 1
            elif response.lower() == 'all':
                current_page = 0
                results_per_page = total_pages  # Set results per page to total results for 'all'
            elif response.lower() == 'done':
                break


def find_similar_words(word, word_list, n=1, cutoff=0.8):
    """
    Find similar words from the word list using difflib.
    """
    return get_close_matches(word, word_list, n=n, cutoff=cutoff)


def get_all_words(text):
    """
    Extract all unique words from the text for similarity comparison.
    """
    words = set()
    for page in text:
        page_words = re.findall(r'\w+', page)
        words.update(page_words)
    return words


def save_pdf_pages(page_numbers):
    input_pdf = PdfReader(PDF_PATH)
    output_pdf = PdfWriter()

    for page_num in page_numbers:
        output_pdf.add_page(input_pdf.pages[page_num - 1])

    with open(RESULT_PDF_PATH, 'wb') as output_pdf_file:
        output_pdf.write(output_pdf_file)
    print(f"Search results saved to {RESULT_PDF_PATH}")


def search_menu():
    if os.path.exists(SERIALIZED_GRAPH_PATH) and os.path.exists(SERIALIZED_TRIE_PATH) and os.path.exists(
            SERIALIZED_TEXT_PATH):
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

    all_words = get_all_words(text)

    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break

        # Check for logical operators in the query
        has_logical_operators = any(op in query.lower() for op in ['and', 'or', 'not'])

        # Autocomplete logic (only if no logical operators are present)
        if not has_logical_operators and query.endswith('*'):
            autocomplete_options = trie.autocomplete(query.rstrip('*'))
            if autocomplete_options:
                print("Autocomplete options:")
                for option in autocomplete_options:
                    print(option)
                autocomplete_choice = input("Choose an option or continue typing your query: ")
                if autocomplete_choice:
                    query = autocomplete_choice

        parsed_query = parse_query(query)
        results, keyword_count, page_order = search_keywords(text, parsed_query, G, trie)

        if not results and not has_logical_operators:  # If no results and no logical operators, suggest similar words
            similar_words = []
            for token in parsed_query:
                if isinstance(token, list):
                    for word in token:
                        similar_word = find_similar_words(word, all_words)
                        if similar_word:
                            similar_words.extend(similar_word)

            if similar_words:
                print("Did you mean:")
                for suggestion in similar_words:
                    print(suggestion)
                continue_choice = input("Would you like to search for one of these suggestions? (yes/no): ")
                if continue_choice.lower() == 'yes':
                    new_query = input("Enter the new search query: ")
                    parsed_query = parse_query(new_query)
                    results, keyword_count, page_order = search_keywords(text, parsed_query, G, trie)

        if results:
            display_results(results, keyword_count, page_order, G, parsed_query, text)
        else:
            print("No results found.")


if __name__ == "__main__":
    search_menu()
