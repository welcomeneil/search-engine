import logging
import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
from tokenizer import tokenize, compute_word_frequencies

logger = logging.getLogger(__name__)


class Crawler:
    """
    This class is responsible for scraping urls from the next available link in frontier and adding the scraped links to
    the frontier
    """

    def __init__(self, frontier, corpus):
        self.frontier = frontier
        self.corpus = corpus
        self.valid_outlinks = {}
        self.subdomains_visited = {}
        self.valid_outlinks = dict()
        self.downloaded_urls = []
        self.trap_urls = []
        self.trap_urls_set = set()
        self.longest_page = ("", 0)
        self.word_frequencies = {}

    def start_crawling(self):
        """
        This method starts the crawling process which is scraping urls from the next available link in frontier and adding
        the scraped links to the frontier
        """
        while self.frontier.has_next_url():
            url = self.frontier.get_next_url()
            self.downloaded_urls.append(url)
            netloc = urlparse(url).netloc
            if netloc[0:3] != "www":
                if netloc not in self.subdomains_visited:
                    self.subdomains_visited[netloc] = 1
                else:
                    self.subdomains_visited[netloc] += 1

            logger.info(
                "Fetching URL %s ... Fetched: %s, Queue size: %s",
                url,
                self.frontier.fetched,
                len(self.frontier),
            )
            url_data = self.corpus.fetch_url(url)

            if url_data.get("url") not in self.valid_outlinks:
                self.valid_outlinks[url_data.get("url")] = 0

            for next_link in self.extract_next_links(url_data):
                if self.is_valid(next_link):
                    if self.corpus.get_file_name(next_link) is not None:
                        self.frontier.add_url(next_link)
                        self.valid_outlinks[url_data.get("url")] += 1
                else:
                    self.trap_urls.append(next_link)
                    self.trap_urls_set.add(next_link)
        self.print_analytics()

    def extract_next_links(self, url_data):
        """
        The url_data coming from the fetch_url method will be given as a parameter to this method. url_data contains the
        fetched url, the url content in binary format, and the size of the content in bytes. This method should return a
        list of urls in their absolute form (some links in the content are relative and needs to be converted to the
        absolute form). Validation of links is done later via is_valid method. It is not required to remove duplicates
        that have already been fetched. The frontier takes care of that.
        Suggested library: lxml
        """
        if (
            url_data["url"] is None
            or url_data["size"] == 0
            or url_data["content_type"] is None
            or url_data["http_code"] == 404
        ):
            return []

        soup = BeautifulSoup(url_data["content"], "html.parser")

        words = soup.get_text(separator=" ").split()
        self.update_longest_page(words, url_data["url"])
        self.update_word_frequencies(words)

        output_links = []
        for link in soup.find_all("a"):
            if url_data["is_redirected"]:
                base_url = url_data["final_url"]
            else:
                base_url = url_data["url"]
            href = urljoin(base_url, link.get("href"))
            output_links.append(href)
        return output_links

    def is_valid(self, url):
        """
        Function returns True or False based on whether the url has to be fetched or not. This is a great place to
        filter out crawler traps. Duplicated urls will be taken care of by frontier. You don't need to check for duplication
        in this method
        """
        if url in self.trap_urls_set:
            return False
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False
        if parsed.netloc == "":
            return False

        try:
            return (
                ".ics.uci.edu" in parsed.hostname
                and not self.is_trap(parsed)
                and not re.match(
                    ".*\.(css|js|bmp|gif|jpe?g|ico"
                    + "|png|tiff?|mid|mp2|mp3|mp4|wmz"
                    + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                    + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1"
                    + "|thmx|mso|arff|rtf|jar|csv"
                    + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf"
                    + "|lif|xml|htm|bam|h|cp|c|hqx|ff|py|.git|.gitignore|odp|java|ai|pov|bib|txt|class|)$",
                    parsed.path.lower(),
                )
            )

        except TypeError:
            print("TypeError for ", parsed)
            return False

    def is_trap(self, parsed):
        """Function returns true or false depending on if it detects a trap from the parsed object"""
        if str(parsed.fragment) != "":
            return True

        path_directories = parsed.path.split("/")
        if (
            len(path_directories) > 6
            or ("pix" in path_directories)
            or ("pairs" in path_directories and "Data" in path_directories)
            or ("archive" in parsed.netloc and "datasets" in parsed.path)
            or ("wics" in parsed.netloc and "events" in path_directories)
            or ("cbcl" in parsed.netloc and "public_data" in path_directories)
            or (
                "fano" in parsed.netloc
                and "ca" in path_directories
                and "rules" in path_directories
            )
        ):
            return True

        queries = parse_qs(parsed.query)
        if (
            len(queries) > 4
            or "ical" in queries
            or "do" in queries
            or "version" in queries
            or "share" in queries
            or (
                "action" in queries
                and (queries["action"][0] in ["login", "download", "edit"])
            )
            or ("from" in queries and re.match("^20\d{2}-", queries["from"][0]))
        ):
            return True

        if self.has_repeating_subdirectories(str(parsed.path).split("/")):
            return True

        return False

    def has_repeating_subdirectories(self, path_list):
        """Function checks if there are more than two repeating subdirectories in the url"""
        max_count = 0
        count = 1
        for i in range(1, len(path_list)):
            if path_list[i] == path_list[i - 1]:
                count += 1
            else:
                max_count = max(max_count, count)
                count = 1
        max_count = max(max_count, count)
        return max_count > 2

    def update_word_frequencies(self, words):
        """Function updates the word frequencies dictionary based on the tokens found in the HTML document"""
        words = tokenize(words)
        compute_word_frequencies(words, frequencies=self.word_frequencies)

    def update_longest_page(self, words, url):
        """Function updates the current longest page"""
        if len(words) > self.longest_page[1]:
            self.longest_page = (url, len(words))

    def print_analytics(self):
        """Print out all five analytics to files"""
        with open("subdomainsVisited.txt", "a") as f:
            for key, val in sorted(
                self.subdomains_visited.items(),
                key=lambda items: (-items[1], items[0]),
            ):
                print(key, "\t", val, sep="", file=f)

        with open("pageWithMostOutlinks.txt", "a") as f:
            print(max(self.valid_outlinks, key=self.valid_outlinks.get), file=f)
            print(max(self.valid_outlinks.values()), "outlinks", file=f)

        with open("downloadedURLs.txt", "a") as f:
            for i in self.downloaded_urls:
                print(i, file=f)

        with open("trapURLs.txt", "a") as f:
            for i in self.trap_urls:
                print(i, file=f)

        with open("longestPage.txt", "a") as f:
            print(self.longest_page[0], file=f)
            print(self.longest_page[1], "words", file=f)

        with open("mostCommonWords.txt", "a") as f:
            count = 0
            for key, val in sorted(
                self.word_frequencies.items(),
                key=lambda items: (-items[1], items[0]),
            ):
                if count == 50:
                    break
                print(key, "\t", val, sep="", file=f)
                count += 1
