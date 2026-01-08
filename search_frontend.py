from flask import Flask, request, jsonify, render_template
from query_engine import SearchEngine
import os

class MyFlaskApp(Flask):
    def run(self, host=None, port=None, debug=None, **options):
        super(MyFlaskApp, self).run(host=host, port=port, debug=debug, **options)

app = MyFlaskApp(__name__,
                 template_folder='Frontend/templates',
                 static_folder='Frontend/static',
                 static_url_path='/static')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Initialize Search Engine
search_engine = SearchEngine()

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/search")
def search():
    ''' Returns up to a 100 search results for the query. '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    res = search_engine.search(query)
    return jsonify(res)

@app.route("/search_body")
def search_body():
    ''' Returns up to a 100 search results for the query using TFIDF AND COSINE SIMILARITY OF THE BODY. '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    res = search_engine.search_body(query)
    return jsonify(res)

@app.route("/search_title")
def search_title():
    ''' Returns search results for title. '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    res = search_engine.search_title(query)
    return jsonify(res)

@app.route("/search_anchor")
def search_anchor():
    ''' Returns search results for anchor. '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    res = search_engine.search_anchor(query)
    return jsonify(res)

@app.route("/get_pagerank", methods=['POST'])
def pagerank():
    ''' Returns PageRank values for a list of provided wiki article IDs. '''
    res = []
    wiki_ids = request.get_json()
    if not wiki_ids or len(wiki_ids) == 0:
      return jsonify(res)
    res = search_engine.get_pagerank(wiki_ids)
    return jsonify(res)

@app.route("/get_pageview", methods=['POST'])
def pageview():
    ''' Returns page views. '''
    res = []
    wiki_ids = request.get_json()
    if not wiki_ids or len(wiki_ids) == 0:
      return jsonify(res)
    res = search_engine.get_pageviews(wiki_ids)
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
