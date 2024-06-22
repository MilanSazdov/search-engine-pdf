import PyPDF2
import re
import networkx as nx
from collections import defaultdict
from termcolor import colored

PDF_PATH = "C:/Users/milan/OneDrive/Desktop/SIIT/2. Semestar/Algoritmi i Strukture/Projekat 2/Data Structures and Algorithms in Python.pdf"
OFFSET = 22  # Offset za prve 22 nenumerisane stranice

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = [page.extract_text() for page in reader.pages]
    return text

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

def search_keywords(text, keywords, G):
    results = defaultdict(list)
    keyword_count = defaultdict(int)
    page_order = []

    for page_num, page in enumerate(text):
        lines = page.split('\n')
        keyword_found = False
        found_keywords = set()

        for line_num, line in enumerate(lines):
            for keyword in keywords:
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

def display_results(results, keyword_count, page_order, G, keywords, text):
    ranked_results = sorted(results.items(), key=lambda x: keyword_count[x[0]], reverse=True)
    for page_num, matches in ranked_results:
        search_result = page_order.index(page_num) + 1  # Find the position in the page_order list
        # Calculate the basic keyword appearances and distinct keyword bonus
        keyword_count_on_page = sum(len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for keyword in keywords)
        num_keywords = sum(1 for keyword in keywords if re.search(keyword, text[page_num - 1], re.IGNORECASE))

        # Calculate link and referring keywords bonuses
        in_edges = G.in_edges(page_num, data=True)
        link_bonus = sum(data['weight'] * 10 for _, _, data in in_edges)
        referring_keywords_bonus = 0
        keyword_details = defaultdict(int)

        for source, _, data in in_edges:
            for keyword in keywords:
                keyword_matches = len(re.findall(keyword, text[source - 1], re.IGNORECASE))
                if keyword_matches:
                    referring_keywords_bonus += keyword_matches * 7  # Calculate bonus correctly
                    keyword_details[source] += keyword_matches

        # Total rank calculation
        total_rank = keyword_count_on_page + num_keywords * 5 + link_bonus + referring_keywords_bonus
        print(f"Search Result: {search_result}, Page: {page_num}, Rank: {total_rank}")
        for line_num, context in matches:
            print(f"{line_num}. {context}")

        if in_edges:
            link_info = ', '.join(f"Page {source} ({data['weight']} times)" for source, _, data in in_edges)
            print(f"Linked from pages: {link_info}")
            for source in keyword_details:
                print(f"Keywords on Page {source}: {keyword_details[source]} times")

        print(
            f"Formula for rank: {keyword_count_on_page} (appearances) + {num_keywords} (distinct keywords) * 5 + {link_bonus} (links bonus) + {referring_keywords_bonus} (referring keywords bonus) = {total_rank}")
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
