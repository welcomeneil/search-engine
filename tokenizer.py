from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from collections import Counter

stopwords_set = set(stopwords.words("english"))


def tokenize(words: list[str]) -> list[str]:
    tokens = []
    lemmatized_words = lemmatize(words)

    for w in lemmatized_words:
        w = w.lower()
        if w.isalnum() and w.isascii() and is_valid_token(w):
            tokens.append(w)
        else:
            curr_word = ""
            for l in w:
                if l.isalnum() and l.isascii():
                    curr_word += l
                else:
                    if is_valid_token(curr_word):
                        tokens.append(curr_word)
                    curr_word = ""
            if is_valid_token(curr_word):
                tokens.append(curr_word)
    return tokens


def compute_word_frequencies(
    tokens: list[str], frequencies: dict[str, int] = {}
) -> dict[str, int]:
    frequencies = Counter(tokens)
    return frequencies


def print_frequencies(frequencies: dict[str, int]):
    for key, val in sorted(
        frequencies.items(), key=lambda items: (-items[1], items[0])
    ):
        print(key, "\t", val, sep="")


def is_valid_token(token: str) -> bool:
    return not is_stop_word(token) and len(token) > 1


def is_stop_word(word: str) -> bool:
    return word in stopwords_set


def lemmatize(tokens: list[str]) -> list[str]:
    # Dictionary with each nltk identifiable part of speech, and its corresponding 'pos' tag.
    # The 'pos' tag will be used as a paramater in the WordNetLemmatizer.lemmatize() function
    # to identify what part of speech the given token is for the greatest lemmatization accuracy.
    # -------------------------------------------------------------------------------------------
    # n noun
    # v verb
    # a adjective
    # r adverb
    lemmatized_tokens = []
    l = WordNetLemmatizer()
    parts_of_speech = {
        "JJ": "a",
        "JJR": "a",
        "JJS": "a",
        "NN": "n",
        "NNP": "n",
        "NNS": "n",
        "RB": "r",
        "RBR": "r",
        "RBS": "r",
        "VBG": "v",
        "VB": "v",
        "VBD": "v",
        "VBG": "v",
        "VBN": "v",
        "VBP": "v",
        "VBZ": "v",
    }

    for w in pos_tag(tokens):
        if w[1] in parts_of_speech:
            word = l.lemmatize(w[0], pos=parts_of_speech[w[1]])
            lemmatized_tokens.append(word)
        else:
            word = l.lemmatize(w[0])
            lemmatized_tokens.append(word)
    return lemmatized_tokens
