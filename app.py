from flask import Flask
from flask import render_template, request, redirect
import logging
import pickle
import requests
import json
import gzip




# main.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
api_key = os.getenv("TMDB_API_KEY")




def fetch_poster(id):

    poster_url = f"https://api.themoviedb.org/3/movie/{id}/images?api_key={api_key}"

    response = requests.get(poster_url)

    if response.status_code == 200:
        poster_data = response.json()
        if poster_data["posters"]:
            poster  = poster_data['posters'][0]
            # Construct the full URL for the poster
            poster_full_url = f"https://image.tmdb.org/t/p/w500{poster['file_path']}"
            return poster_full_url
        else:
            print("No posters found for this movie.")
            return None
    else:
        print("Failed to retrieve poster data:", response.status_code)
    

with open("model/movie_dataframe.pkl" , 'rb') as file:
    movies_df = pickle.load(file)

with gzip.open('model/similarity.pkl.gz', 'rb') as f:
    similarity_matrix = pickle.load(f)


def recommend(movie_name):
    index = movies_df[movies_df['original_title'] == movie_name].index[0]
    similarity_wise_min_distance = sorted(list(enumerate(similarity_matrix[index])), reverse=True, key=lambda x:x[1])
    recomended_movies_name = []
    recomended_movies_poster = []
    for i in similarity_wise_min_distance[1:6]:
        movie_id = movies_df.iloc[i[0]].id
        recomended_movies_poster.append(fetch_poster(movie_id))
        recomended_movies_name.append(movies_df.iloc[i[0]].original_title)
    return recomended_movies_name, recomended_movies_poster

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")



@app.route('/recommender', methods=['GET','POST'])
def recommender():
    movies_list = movies_df['original_title'].values
    flag = False
    selected = None
    if request.method == 'POST':
        try:
            if request.form:
                movies_name = request.form.get('movie', default=None)
                selected = movies_name
                # print(movies_name)
                recomended_movies_name, recomended_movies_poster = recommend(movies_name)
                flag = True
                return render_template("prediction.html", movies_name=recomended_movies_name, posters = recomended_movies_poster, movies_list=movies_list, flag=flag, selected=selected)

        except Exception as e:
            logging.error(f"There is an exception in the form request {e}")
            error = f"Error: {e}"
            return render_template("prediction.html", movies_list=movies_list, flag=flag, error=error)
    return render_template("prediction.html", movies_list=movies_list, flag=flag)


if __name__ == "__main__":
    app.run(debug=True)

