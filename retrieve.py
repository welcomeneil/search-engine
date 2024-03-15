import json
import sys
from flask import Flask, render_template, request, send_from_directory
from ranker import Ranker
import timeit
import os

app = Flask(__name__)

index = json.load(open("index.json"))
lengths = json.load(open("lengths.json"))
bigramsIndex = json.load(open("index2.json"))
bigramsLengths = json.load(open("lengths2.json"))
corpusSize = int(open("size.json").read())
bookkeeping = json.load(open("WEBPAGES_RAW/bookkeeping.json"))
ranker = Ranker()


@app.route("/", methods=["GET"])
def search():
    start = timeit.default_timer()
    args = request.args
    results = []
    snippets = []
    query = ""
    offset = 0
    ranker.num_results = 0
    print(args, file=sys.stderr)
    if "search" in args:
        if "page" in args:
            offset = int(args["page"]) * 20
        results = ranker.getRankedResults(
            index,
            corpusSize,
            lengths,
            bigramsIndex,
            bigramsLengths,
            bookkeeping,
            args["search"],
            offset,
        )
        snippets = ranker.getSnippets()
        query = args["search"]
    stop = timeit.default_timer()
    query_time = round(stop - start, 2)
    return render_template(
        "index.html",
        num_results=ranker.num_results,
        results=results,
        snippets=snippets,
        query=query,
        query_time=query_time,
        page=offset // 20,
    )


@app.route("/favicon.ico")
def fav():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")
