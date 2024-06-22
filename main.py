import PyPDF2
import re
from collections import defaultdict
from termcolor import colored

# Path to the PDF file
PDF_PATH = "C:/Users/milan/OneDrive/Desktop/SIIT/2. Semestar/Algoritmi i Strukture/Projekat 2/Data Structures and Algorithms in Python.pdf"

OFFSET = 22  # Offset za prve 22 nenumerisane stranice


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
    links = defaultdict(lambda: defaultdict(int))  # Changed to count occurrences

    # Specifični obrasci za prepoznavanje linkova ka stranicama
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
        lines = page.split('\n')
        keyword_found = False
        found_keywords = set()

        for line_num, line in enumerate(lines):
            # Pronalaženje i beleženje linkova ka drugim stranicama
            for match in link_pattern.finditer(line):
                for i in range(1, len(match.groups()) + 1):
                    if match.group(i) is not None:
                        try:
                            linked_page = int(match.group(i)) + OFFSET  # Dodavanje offseta za linkovane stranice
                            links[linked_page][page_num + 1] += 1
                        except ValueError:
                            continue

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
    link_bonus = defaultdict(int)
    for linked_page, referring_pages in links.items():
        for referring_page, count in referring_pages.items():
            keyword_count[linked_page] += count * 10  # Veći multiplikator za linkove
            link_bonus[linked_page] += sum(
                len(re.findall(keyword, text[referring_page - 1], re.IGNORECASE)) for keyword in
                keywords) * 7  # Dodavanje poena za broj ključnih reči na stranicama koje sadrže vezu

    for page in keyword_count:
        keyword_count[page] += link_bonus[page]

    return results, keyword_count, page_order, links


def rank_results(results, keyword_count):
    ranked_results = sorted(results.items(), key=lambda x: keyword_count[x[0]], reverse=True)
    return ranked_results


def display_results(results, keyword_count, page_order, links, keywords, text):
    for rank, (page_num, matches) in enumerate(results, start=1):
        search_result = page_order.index(page_num) + 1
        keyword_count_on_page = sum(
            len(re.findall(keyword, text[page_num - 1], re.IGNORECASE)) for keyword in keywords)
        num_keywords = sum(1 for keyword in keywords if re.search(keyword, text[page_num - 1], re.IGNORECASE))
        link_bonus = sum(links[page_num][page] * 10 for page in links[page_num])
        referring_keywords_bonus = sum(
            len(re.findall(keyword, text[page - 1], re.IGNORECASE)) * 7 for page in links[page_num] for keyword in
            keywords)
        total_rank = keyword_count_on_page + num_keywords * 5 + link_bonus + referring_keywords_bonus

        print(f"Search Result: {search_result}, Page: {page_num}, Rank: {total_rank}")
        for line_num, context in matches:
            print(f"{line_num}. {context}")
        if page_num in links:
            link_info = ', '.join(f"{page} ({count} times)" for page, count in links[page_num].items())
            print(f"Links from pages: {link_info}")
        print(
            f"Formula for rank: {keyword_count_on_page} (appearances) + {num_keywords} (distinct keywords) * 5 + {link_bonus} (links bonus) + {referring_keywords_bonus} (referring keywords bonus) = {total_rank}")
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
        display_results(ranked_results, keyword_count, page_order, links, keywords, text)


if __name__ == "__main__":
    search_menu()