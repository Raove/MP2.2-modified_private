import math
import sys
import time
import metapy
import pytoml

class InL2Ranker(metapy.index.RankingFunction):
    """
    Create a new ranking function in Python that can be used in MeTA.
    """
    def __init__(self, some_param=1.0):
        self.param = some_param
        # You *must* call the base class constructor here!
        super(InL2Ranker, self).__init__()

    def score_one(self, sd):
        """
        You need to override this function to return a score for a single term.
        For fields available in the score_data sd object,
        @see https://meta-toolkit.org/doxygen/structmeta_1_1index_1_1score__data.html
        """
        score = 0
        # Q = "query"
        # D = "document"
        # t = "term"
        # N = "number of docs in corpus C"
        # avgdl = "length"
        # c > 0
        # C = "corpus"
        # ctD = "query term count"
        # ctC = "number of times term t appears in the corpus"
        
        D = sd.doc_size
        t = sd.t_id
        avgdl = sd.avg_dl
        N = sd.num_docs
        ctD = sd.doc_term_count
        ctC = sd.corpus_term_count
        tfn = ctD * math.log(1 + (avgdl / abs(D)), 2)
        score = sd.query_term_weight * (tfn / (tfn + self.param)) * math.log((N + 1) / (ctC + 0.5),2)
        
        return score
        # return (self.param + sd.doc_term_count) / (self.param * sd.doc_unique_terms + sd.doc_size)


# def load_ranker(cfg_file, k1, b, idf):
def load_ranker(cfg_file):
    """
    Use this function to return the Ranker object to evaluate, 
    The parameter to this function, cfg_file, is the path to a
    configuration file used to load the index.
    """
    #BM25
    k1 = 1.90079
    b = 0.743
    idf = 114
    #PivotedLength
    s = 0.2
    #AbsoluteDiscount
    delta = 0.7
    #JelinkMercer
    lambda1 = 0.7
    #DirichletPrior
    mu = 2000

    return metapy.index.OkapiBM25(k1, b, idf)
    # return metapy.index.PivotedLength(s)
    # return metapy.index.AbsoluteDiscount(delta)
    # return metapy.index.JelinekMercer(lambda1)
    # return metapy.index.DirichletPrior(mu)
    # return InL2Ranker()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: {} config.toml".format(sys.argv[0]))
        sys.exit(1)

    cfg = sys.argv[1]
    print('Building or loading index...')
    # k1 = 1.89
    # b = 0.7
    # idf = 100
    # best = 0
    # while k1 <= 1.93:        
    #     print("k1 :", k1)
    #     b = 0.7
    #     while b <= 0.8:
    #         print("b :",b)
    #         idf = 100
    #         while idf <= 500:
    idx = metapy.index.make_inverted_index(cfg)
    # ranker = load_ranker(cfg, k1, b, idf)
    ranker = load_ranker(cfg)
    ev = metapy.index.IREval(cfg)

    with open(cfg, 'r') as fin:
        cfg_d = pytoml.load(fin)

    query_cfg = cfg_d['query-runner']
    if query_cfg is None:
        print("query-runner table needed in {}".format(cfg))
        sys.exit(1)

    start_time = time.time()
    top_k = 10
    query_path = query_cfg.get('query-path', 'queries.txt')
    query_start = query_cfg.get('query-id-start', 0)

    query = metapy.index.Document()
    ndcg = 0.0
    num_queries = 0
    print('Running queries')
    with open(query_path) as query_file:
        for query_num, line in enumerate(query_file):
            query.content(line.strip())
            results = ranker.score(idx, query, top_k)
            ndcg += ev.ndcg(results, query_start + query_num, top_k)
            num_queries+=1
    ndcg= ndcg / num_queries
            
    print("NDCG@{}: {}".format(top_k, ndcg))
    print("Elapsed: {} seconds".format(round(time.time() - start_time, 4)))
    #             if ndcg > best:
    #                 best = ndcg 
    #                 highestk1 = k1
    #                 highestb = b
    #                 highestidf = idf
    #             idf += 1
    #         b += 0.01
    #     k1 += 0.001
    # print("Highest NDCG and best ", highestk1, highestb, highestidf, best)
