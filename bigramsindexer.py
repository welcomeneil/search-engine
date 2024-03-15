from indexer import Indexer
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from tokenizer import tokenize, compute_word_frequencies
from nltk import bigrams
from collections import Counter
import timeit
import sys
import json


class BigramsIndexer(Indexer):
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
                word_frequencies = compute_word_frequencies(bigrams(tokens))
                weighted_words = self.extract_weighted_tags(soup)
                raw_tfs = dict(Counter(word_frequencies) + Counter(weighted_words))
                if not tokens:
                    continue
                key1 = tokens[0]
                for i in range(1, len(tokens)):
                    key2 = tokens[i]
                    key = f"{key1} {key2}"
                    doc_key = str(folder_num) + "/" + str(file_num)
                    wf_key = (key1, key2)
                    raw_tf = raw_tfs[wf_key]
                    pair = [doc_key, raw_tf, 0]
                    if key not in self.index:
                        self.index[key] = [pair]
                    else:
                        if self.index[key][-1][0] != doc_key:
                            self.index[key].append(pair)
                    key1 = key2
                print("Folder", folder_num, "File", file_num)

    def extract_weighted_tags(self, soup):
        weighted_tag_words = {}
        for tag in self.tags:
            words = []
            for i in soup.find_all(tag):
                words += word_tokenize(i.text.strip())
            for word in bigrams(tokenize(words)):
                if word not in weighted_tag_words:
                    weighted_tag_words[word] = self.tags[tag]
                else:
                    weighted_tag_words[word] += self.tags[tag]
        return weighted_tag_words


if __name__ == "__main__":
    start = timeit.default_timer()
    base_url = sys.argv[1]
    indexer = BigramsIndexer(base_url)
    indexer.create_index()
    with open("index2.json", "a") as f:
        json.dump(indexer.get_index(), f, indent=4)
    with open("lengths2.json", "a") as f:
        json.dump(indexer.get_lengths(), f, indent=4)
    stop = timeit.default_timer()
    print("Time: ", stop - start, "seconds")
