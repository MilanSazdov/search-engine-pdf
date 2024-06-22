import PyPDF2
import re
from collections import defaultdict
from termcolor import colored

# Path to the PDF file
PDF_PATH = "C:/Users/milan/OneDrive/Desktop/SIIT/2. Semestar/Algoritmi i Strukture/Projekat 2/Data Structures and Algorithms in Python.pdf"


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = []
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text.append(page.extract_text())
    return text


def highlight_keyword(text, keyword):
    highlighted = text.replace(keyword, f"\033[91m{keyword}\033[0m")
    return highlighted


def search_keywords(text, keywords):
    results = defaultdict(list)
    keyword_count = defaultdict(int)
    page_order = []
    links = defaultdict(set)

    link_pattern = re.compile(r'page\s+(\d+)', re.IGNORECASE)

    for page_num, page in enumerate(text):
        lines = page.split('\n')
        keyword_found = False
        found_keywords = set()

        for line_num, line in enumerate(lines):
            # Pronalaženje i beleženje linkova ka drugim stranicama
            for match in link_pattern.finditer(line):
                linked_page = int(match.group(1))
                links[linked_page].add(page_num + 1)

            for keyword in keywords:
                if re.search(keyword, line, re.IGNORECASE):
                    context_highlighted = re.sub(keyword, lambda x: f"\033[91m{x.group()}\033[0m", line,
                                                 flags=re.IGNORECASE)
                    results[page_num + 1].append((line_num + 1, context_highlighted))
                    keyword_count[page_num + 1] += len(re.findall(keyword, line, re.IGNORECASE))
                    found_keywords.add(keyword)
                    if not keyword_found:
                        page_order.append(page_num + 1)
                        keyword_found = True

        # Dodavanje bonus poena za stranice koje sadrže više različitih ključnih reči
        keyword_count[page_num + 1] += len(found_keywords) * 5  # Multiplikator se može prilagoditi

    # Dodavanje poena na osnovu linkova ka stranicama
    for linked_page, referring_pages in links.items():
        for referring_page in referring_pages:
            keyword_count[linked_page] += len(keywords) * 10  # Veći multiplikator za linkove

    return results, keyword_count, page_order, links


def rank_results(results, keyword_count):
    ranked_results = sorted(results.items(), key=lambda x: keyword_count[x[0]], reverse=True)
    return ranked_results


def display_results(results, keyword_count, page_order, links):
    for rank, (page_num, matches) in enumerate(results, start=1):
        search_result = page_order.index(page_num) + 1
        print(f"Search Result: {search_result}, Page: {page_num}, Rank: {keyword_count[page_num]}")
        for line_num, context in matches:
            print(f"{line_num}. {context}")
        if page_num in links:
            print(f"Links from pages: {', '.join(map(str, links[page_num]))}")
        print()


def search_menu():
    text = extract_text_from_pdf(PDF_PATH)
    while True:
        query = input("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        keywords = query.split()
        results, keyword_count, page_order, links = search_keywords(text, keywords)
        ranked_results = rank_results(results, keyword_count)
        display_results(ranked_results, keyword_count, page_order, links)


if __name__ == "__main__":
    search_menu()
