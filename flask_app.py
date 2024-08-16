from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import sys
import os

sys.path.append(os.path.abspath('models'))
from user_user_cf import UserUserCF

app = Flask(__name__)

# Load your trained model
recommender = UserUserCF("data/interactions.csv", "data/book_id_map.csv", "data/book_works.csv", "data/isbn.csv")

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        user_ratings = request.json['user_ratings']  # Expecting a list of user ratings in the POST request
        new_user_ratings = pd.DataFrame(user_ratings)
        
        recommendations = recommender.recommend_books(new_user_ratings, n=20)
        
        return jsonify(recommendations)
    except Exception as e:
        # Catch any errors and return them as JSON
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)