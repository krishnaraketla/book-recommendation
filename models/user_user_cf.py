import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
import csv

class UserUserCF:
    def __init__(self, interactions_path, book_id_map_path, book_works_path, isbn_path):
        # Load the data
        self.interactions = pd.read_csv(interactions_path)
        self.book_id_map_df = pd.read_csv(book_id_map_path)
        self.book_works_df = pd.read_csv(book_works_path)
        self.isbn_path = isbn_path

        # Create a mapping from CSV book IDs to book IDs
        self.book_id_map = dict(zip(self.book_id_map_df['book_id_csv'], self.book_id_map_df['book_id']))

        # Build the user-item matrix
        self.user_item_csr, self.book_rating_counts, self.columns = self.build_user_item_matrix(self.interactions)

    def get_best_book_id(self, book_id):
        return self.book_id_map[book_id]
    
    def get_work_id(self, best_book_id):
        match = self.book_works_df[self.book_works_df['best_book_id'] == best_book_id]
        if not match.empty:
            return match['work_id'].values[0]
        else:
            return None

    def get_original_title_by_book_id(self, best_book_id):
        match = self.book_works_df[self.book_works_df['best_book_id'] == best_book_id]
        if not match.empty:
            return match['original_title'].values[0]
        else:
            return None
        
    def find_isbn_by_work_and_book_id(self, target_work_id, target_book_id):
        # Open and read the CSV file
        with open(self.isbn_path, 'r') as f:
            reader = csv.DictReader(f)
            
            # Iterate over each row in the CSV file
            for row in reader:
                if row['book_id'] == target_book_id:
                    # Return the matching ISBN
                    return row['isbn']
        
        # Return None if no match is found
        return None

    def build_user_item_matrix(self, interactions):
        user_item_matrix = interactions.pivot(index='user_id', columns='book_id', values='rating')
        
        user_means = user_item_matrix.mean(axis=1)
        user_std_d = user_item_matrix.std(axis=1)
        # user_std_d_replaced = user_std_d.replace(0, 1e-10)
        
        user_item_matrix = user_item_matrix.sub(user_means, axis=0)
        # user_item_matrix = user_item_matrix.div(user_std_d_replaced, axis=0)
        
        # Count number of ratings a book has received
        book_rating_counts = ((user_item_matrix != 0) & (user_item_matrix.notna())).sum(axis=0)
        
        user_item_matrix = user_item_matrix.fillna(0)
        
        # Normalize the ratings by dividing by the book rating counts
        normalized_user_item_matrix = user_item_matrix.div(book_rating_counts, axis=1).fillna(0)
        
        user_item_csr = csr_matrix(normalized_user_item_matrix.values)
        
        return user_item_csr, book_rating_counts, user_item_matrix.columns

    def predict_new_ratings(self, new_user_csr, similarities):
        new_user_dense = new_user_csr.toarray()
        user_item_dense = self.user_item_csr.toarray()
        
        predicted_ratings = new_user_dense.copy()
        
        for book_idx in range(new_user_dense.shape[1]):
            if new_user_dense[0, book_idx] == 0:
                book_ratings = user_item_dense[:, book_idx]
                
                user_similarities = similarities[0]
                
                valid_similarities = user_similarities[user_similarities >= 0]
                valid_book_ratings = book_ratings[user_similarities >= 0]
                
                weighted_sum = np.dot(valid_similarities, valid_book_ratings)
                sum_of_weights = np.sum(np.abs(valid_similarities))
                
                if sum_of_weights != 0:
                    predicted_rating = weighted_sum / sum_of_weights
                else:
                    predicted_rating = 0
                
                predicted_ratings[0, book_idx] = predicted_rating
        
        return predicted_ratings

    def get_top_n_predictions(self, new_user_csr, similarities, n=10):
        predicted_ratings = self.predict_new_ratings(new_user_csr, similarities)
        
        predicted_ratings = predicted_ratings.flatten()
        
        rated_indices = new_user_csr.nonzero()[1]
        
        predicted_ratings[rated_indices] = -np.inf
        
        top_n_indices = np.argsort(predicted_ratings)[-n:][::-1]
        
        top_n_ratings = predicted_ratings[top_n_indices]
        
        return top_n_indices, top_n_ratings

    def recommend_books(self, new_user_ratings, n=10):
        new_user_matrix = new_user_ratings.pivot(index='user_id', columns='book_id', values='rating')
        
        new_user_matrix = new_user_matrix.reindex(columns=self.columns)
        
        new_user_means = new_user_matrix.mean(axis=1)
        new_user_matrix = new_user_matrix.sub(new_user_means, axis=0)
        
        new_user_matrix = new_user_matrix.fillna(0)
        
        new_user_csr = csr_matrix(new_user_matrix.values)
        
        similarities = cosine_similarity(new_user_csr, self.user_item_csr)
        
        top_n_indices, top_n_ratings = self.get_top_n_predictions(new_user_csr, similarities, n=n)
        
        top_n_book_ids = self.columns[top_n_indices]
        
        top_n_ratings_denormalized = top_n_ratings + new_user_means.values[0]
        
        recommendations = []
        for book_id, rating in zip(top_n_book_ids, top_n_ratings_denormalized):
            best_book_id = self.get_best_book_id(book_id)
            title = self.get_original_title_by_book_id(best_book_id)
            
            # Handle null, NaN, and empty titles
            if title is None or pd.isna(title):
                title = "Unknown Title"
            
            work_id = self.get_work_id(best_book_id)
            isbn = self.find_isbn_by_work_and_book_id(str(work_id), str(best_book_id))
            
            recommendations.append({
                "isbn": isbn if isbn else "Unknown ISBN",  # Handle empty ISBNs
                "title": title,
                "predicted_rating": round(rating, 2)
            })
        return recommendations
            
    def split_data(self):
        # Splitting the interactions data into training and testing sets
        train, test = train_test_split(self.interactions, test_size=0.2, random_state=42)
        return train, test

    def train_model(self, train_data):
        # Use the train data to build the user-item matrix
        self.user_item_csr, self.book_rating_counts, self.columns = self.build_user_item_matrix(train_data)

    def evaluate(self):
        # Split the data
        train, test = self.split_data()
        
        # Train the model with the training set
        self.train_model(train)

        # Prepare the test data
        test_user_item_matrix = test.pivot(index='user_id', columns='book_id', values='rating')
        # Ensure the test matrix has the same columns as the training matrix
        test_user_item_matrix = test_user_item_matrix.reindex(columns=self.columns)
        
        test_user_means = test_user_item_matrix.mean(axis=1)
        test_user_item_matrix = test_user_item_matrix.sub(test_user_means, axis=0)
        
        test_user_item_matrix = test_user_item_matrix.fillna(0)
        
        test_csr = csr_matrix(test_user_item_matrix.values)
        
        # Get cosine similarity
        similarities = cosine_similarity(test_csr, self.user_item_csr)
        
        # Predict the ratings
        hit_count = 0
        total = 0
        
        for idx in range(test_csr.shape[0]):
            top_n_indices, top_n_ratings = self.get_top_n_predictions(test_csr[idx], similarities, n=100)
            true_books = test_csr[idx].nonzero()[1]
                        
            # Calculate the hit rate
            hits = len(set(top_n_indices) & set(true_books))
            if len(true_books) > 0:
                print("yes, ",hits)
                hit_count += hits
                total += len(true_books)
        
        # Calculating the hit rate
        hit_rate = hit_count
        return hit_rate

# Example usage:
if __name__ == "__main__":
    # Create an instance of the UserUserCF class
    recommender = UserUserCF("data/interactions.csv", "data/book_id_map.csv", "data/book_works.csv", "data/isbn.csv")
    
    # New user ratings
    new_user_ratings = pd.DataFrame({
        'user_id': [9999999999] * 9,
        'book_id': [7300, 1201, 100385, 530615, 48625, 14870, 7170, 19782, 1146577],
        'rating': [5, 3, 4, 4, 3, 2, 1, 3, 5]
    })
    
    print("Books you have rated:")
    for idx, row in new_user_ratings.iterrows():
        best_book_id = recommender.get_best_book_id(row['book_id'])
        title = recommender.get_original_title_by_book_id(best_book_id)
        work_id = recommender.get_work_id(best_book_id)
        isbn = recommender.find_isbn_by_work_and_book_id(str(work_id), str(best_book_id))
        # print(f"Book ID: {best_book_id}, Work ID: {work_id}, Title: {title}, Rating: {row['rating']}")
        print(f"ISBN: {isbn}, Title: {title}, Rating: {row['rating']}")
    
    # Get recommendations for the new user
    recommendations = recommender.recommend_books(new_user_ratings, n=20)
    