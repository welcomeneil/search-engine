from collections import defaultdict
import math
from bs4 import BeautifulSoup


class Ranker:
    def __init__(self):
        self.num_results = 0
        self.docs = []

    def getRankedResults(
        self,
        index,
        corpusSize,
        lengths,
        bigramsIndex,
        bigramsLengths,
        bookkeeping,
        query,
        offset,
    ):
        self.docs = []
        scores = defaultdict(int)
        query = query.lower()
        for term in query.split():
            if term not in index.keys():
                continue
            weight_tq = 1 * math.log(corpusSize / len(index[term]))
            for doc in index[term]:
                weight_td = doc[2]
                scores[doc[0]] += weight_tq * weight_td

        bigramsScores = defaultdict(int)
        terms = query.split()
        for term in list(map(" ".join, zip(terms[:-1], terms[1:]))):
            if term not in bigramsIndex.keys():
                continue
            weight_tq = 1 * math.log(corpusSize / len(bigramsIndex[term]))
            for doc in bigramsIndex[term]:
                weight_td = doc[2]
                bigramsScores[doc[0]] += weight_tq * weight_td

        if not scores:
            self.num_results = 0
            return []
        else:
            self.num_results = len(scores)
            for doc in scores:
                scores[doc] = scores[doc] / lengths[doc]
                if doc in bigramsLengths:
                    scores[doc] += bigramsScores[doc] / bigramsLengths[doc]

            url_results = []
            counter = 0
            scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
            for doc_key in list(scores.keys())[offset:]:
                self.docs.append(doc_key)
                url_results.append(bookkeeping[doc_key])
                counter += 1
                if counter == 20:
                    break
            return url_results

    def getSnippets(self):
        snippets = []
        for i in self.docs:
            soup = BeautifulSoup(open(f"WEBPAGES_RAW/{i}"), "html.parser")
            title = soup.find("title")
            description = soup.get_text().strip()
            if title:
                snippets.append([title.text, description])
            else:
                snippets.append(["", ""])
        return snippets
