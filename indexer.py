import sys
from bs4 import BeautifulSoup
from tokenizer import tokenize, compute_word_frequencies
import json
import timeit
from nltk.tokenize import word_tokenize
import math
from collections import defaultdict, Counter


class Indexer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.index = {}
        self.num_documents = 0
        self.document_frequencies = {}
        self.lengths = defaultdict(float)
        self.tags = {"title": 3, "h1": 3, "h2": 2, "a": 2, "h3": 1, "b": 1}

    def create_index(self):
        try:
            self.first_pass()
        except FileNotFoundError:
            pass
        self.calculate_document_frequencies()
        self.calculate_num_documents()
        self.second_pass()
        self.normalize_lengths()

    def first_pass(self):
        for folder_num in range(0, 75):
            for file_num in range(0, 500):
                full_path = "/".join([self.base_url, str(folder_num), str(file_num)])
                content = ""
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                soup = BeautifulSoup(content, "html.parser")
                words = word_tokenize(soup.get_text(separator=" "))
                tokens = tokenize(words)
                word_frequencies = compute_word_frequencies(tokens)
                weighted_words = self.extract_weighted_tags(soup)
                raw_tfs = dict(Counter(word_frequencies) + Counter(weighted_words))
                for key in tokens:
                    doc_key = str(folder_num) + "/" + str(file_num)
                    raw_tf = raw_tfs[key]
                    pair = [doc_key, raw_tf, 0]
                    if key not in self.index:
                        self.index[key] = [pair]
                    else:
                        if self.index[key][-1][0] != doc_key:
                            self.index[key].append(pair)
                print("Folder", folder_num, "File", file_num)

    def extract_weighted_tags(self, soup):
        weighted_tag_words = {}
        for tag in self.tags:
            words = []
            for i in soup.find_all(tag):
                words += word_tokenize(i.text.strip())
            for word in tokenize(words):
                if word not in weighted_tag_words:
                    weighted_tag_words[word] = self.tags[tag]
                else:
                    weighted_tag_words[word] += self.tags[tag]
        return weighted_tag_words

    def calculate_num_documents(self):
        s = set()
        for val in self.index.values():
            for doc in val:
                s.add(doc[0])
        self.num_documents = len(s)

    def calculate_document_frequencies(self):
        for key in self.index:
            self.document_frequencies[key] = len(self.index[key])

    def second_pass(self):
        for key in self.index:
            df = self.document_frequencies[key]
            for i in range(len(self.index[key])):
                doc_key = self.index[key][i][0]
                raw_tf = self.index[key][i][1]
                tf_idf = self.calculate_tf_idf(raw_tf, df)
                self.index[key][i][2] = tf_idf
                self.lengths[doc_key] += tf_idf**2

    def calculate_tf_idf(self, raw_tf, df):
        tf = 1 + math.log10(raw_tf)
        idf = math.log10(self.num_documents / df)
        return tf * idf

    def normalize_lengths(self):
        for i in self.lengths:
            self.lengths[i] = math.log10(math.sqrt(self.lengths[i]))

    def get_index(self):
        return self.index

    def get_num_documents(self):
        return self.num_documents

    def get_document_frequencies(self):
        return self.document_frequencies

    def get_lengths(self):
        return self.lengths


if __name__ == "__main__":
    start = timeit.default_timer()
    base_url = sys.argv[1]
    indexer = Indexer(base_url)
    indexer.create_index()
    with open("index.json", "a") as f:
        json.dump(indexer.get_index(), f, indent=4)
    with open("lengths.json", "a") as f:
        json.dump(indexer.get_lengths(), f, indent=4)
    with open("size.json", "a") as f:
        json.dump(indexer.get_num_documents, f, indent=4)
    stop = timeit.default_timer()
    print("Time: ", stop - start, "seconds")
