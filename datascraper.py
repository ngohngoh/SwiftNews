import pandas as pd
import numpy as np
import glob 
import os
import re

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from nltk.corpus import stopwords
from scipy.sparse import coo_matrix

def data_transform(folder_dir):

    print("folder_dir:", folder_dir)
    file_list = glob.glob(os.path.join(folder_dir, "*.txt"))

    news = []
 
    for file_path in file_list:
        with open(file_path) as f_input:
            article = f_input.read().split("\n")
            article = " ".join(article)
            news.append(article)

    df = pd.DataFrame(np.array(news))
    pd.set_option('display.max_colwidth', -1)
    df.rename(columns={0:'description'}, inplace=True)

    stop_words = set(stopwords.words("english"))
    # stop_words = list(stop_words).extend(["rdquo","ldquo"])
    cv=CountVectorizer(max_df=0.8,stop_words="english", max_features=10000, ngram_range=(1,3))
    X=cv.fit_transform(df['description'])

    tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True)
    tfidf_transformer.fit(X)
    # get feature names
    feature_names=cv.get_feature_names()
    
    # fetch document for which keywords needs to be extracted
    doc=df['description'][1]
    
    #generate tf-idf for the given document
    tf_idf_vector=tfidf_transformer.transform(cv.transform([doc]))

    def sort_coo(coo_matrix):
        tuples = zip(coo_matrix.col, coo_matrix.data)
        return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)
    
    def extract_topn_from_vector(feature_names, sorted_items, topn=5):
        """get the feature names and tf-idf score of top n items"""
        
        #use only topn items from vector
        sorted_items = sorted_items[:topn]
    
        score_vals = []
        feature_vals = []
        
        # word index and corresponding tf-idf score
        for idx, score in sorted_items:
            
            #keep track of feature name and its corresponding score
            score_vals.append(round(score, 3))
            feature_vals.append(feature_names[idx])
    
        #create a tuples of feature,score
        #results = zip(feature_vals,score_vals)
        results= {}
        for idx in range(len(feature_vals)):
            results[feature_vals[idx]]=score_vals[idx]
        
        return results

    final_list = []
    for i in range(df.shape[0]):
        doc = df['description'][i]
        tf_idf_vector=tfidf_transformer.transform(cv.transform([doc]))
        
        #sort the tf-idf vectors by descending order of scores
        sorted_items=sort_coo(tf_idf_vector.tocoo())

        #extract only the top n; n here is 10

        keywords=extract_topn_from_vector(feature_names,sorted_items,10)
        final = list(keywords.keys())
        final_list.append(final)
    #     df.loc[i, 'keywords'] = final

    df["keywords"] = pd.Series(final_list)

    folder_name = folder_dir.split("\\")[-1]
    print("folder_name:", folder_name)

    df.to_pickle("database/" + folder_name + ".pkl")

    return("Data transformed and stored in to 'database' folder!")