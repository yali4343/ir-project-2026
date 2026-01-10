import os

try:
    from gensim.models import KeyedVectors
except ImportError:
    KeyedVectors = None


class SemanticExpander:
    def __init__(self, model_path="data/word2vec.model", topn=3, threshold=0.3):
        self.model = None
        self.topn = topn
        self.threshold = threshold
        self.model_loaded = False

        # Lazy load or load at init
        if KeyedVectors and os.path.exists(model_path):
            try:
                print(f"Loading Word2Vec model from {model_path}...")
                # Assuming KeyedVectors format (GLOVE or Word2Vec KeyedVectors)
                # If it's a full model, KeyedVectors.load might differ, but load_word2vec_format is common
                # We'll try loading as generic KeyedVectors (native gensim or other)
                try:
                    self.model = KeyedVectors.load(model_path)
                except:
                    self.model = KeyedVectors.load_word2vec_format(
                        model_path, binary=True
                    )
                self.model_loaded = True
                print("Word2Vec model loaded successfully.")
            except Exception as e:
                print(f"Failed to load Word2Vec model: {e}")

    def expand(self, query_tokens):
        """
        Expands the query tokens using the loaded Word2Vec model.
        Returns a list of expansion tokens (without the original ones).
        """
        if not self.model_loaded or not self.model:
            return []

        # Logic: find similar words to the query tokens (average of vectors or individual)
        # Expansion budget: small (topn)

        expansion_candidates = []
        try:
            # Filter tokens in vocabulary
            valid_tokens = [t for t in query_tokens if t in self.model]
            if not valid_tokens:
                return []

            # Get most similar to the set of tokens (positive=[...])
            similar_words = self.model.most_similar(
                positive=valid_tokens, topn=self.topn
            )

            for word, score in similar_words:
                # heuristic: threshold and ensure not already in query
                if score >= self.threshold and word not in query_tokens:
                    expansion_candidates.append(word)

        except Exception as e:
            # Fallback/Log
            pass

        return expansion_candidates
