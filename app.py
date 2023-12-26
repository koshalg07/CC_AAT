from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from pymongo import MongoClient
from bson import ObjectId
from json import JSONEncoder
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://koshal:koshal@cluster0.eclu43o.mongodb.net/?retryWrites=true&w=majority")
db = client["AAT"]
movies_collection = db["movies"]

# Custom JSON encoder to handle ObjectId and datetime serialization
class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, datetime):
            return o.strftime("%d-%m-%Y")
        return super().default(o)

app.json_encoder = CustomJSONEncoder

# Function to get the first five movies in the database
def get_top_five_movies():
    return movies_collection.find().sort("Release_Date", -1).limit(5)

# Function to get all movies in the database
def get_all_movies():
    return movies_collection.find()

# Function to add a new movie to the database
def add_movie(title, release_date, language, genre, rotten_tomatoes):
    new_movie = {
        "Title": title,
        "Release_Date": datetime.strptime(release_date, "%Y-%m-%d"),
        "Original_Language": language,
        "Genre": genre,
        "Rotten_Tomatoes": rotten_tomatoes,
    }
    movies_collection.insert_one(new_movie)

# Function to delete a movie from the database
def delete_movie(title, release_date):
    result = movies_collection.delete_one({"Title": title, "Release_Date": datetime.strptime(release_date, "%Y-%m-%d")})
    return result.deleted_count

# Function to update a movie in the database
def update_movie(title, release_date, new_data, new_release_date):
    result = movies_collection.update_one(
        {"Title": title, "Release_Date": release_date},
        {"$set": {**new_data, "Release_Date": new_release_date}}
    )
    return result.modified_count

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_all_movies')
def get_all_movies_page():
    return render_template('all_movies.html')

@app.route('/get_all_movies_data')
def get_all_movies_data():
    all_movies = get_all_movies()
    movies_data = list(all_movies)
    return jsonify(movies_data)

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie_route():
    if request.method == 'POST':
        title = request.form['title']
        release_date = request.form['release_date']
        language = request.form['language']
        genre = request.form['genre']
        rotten_tomatoes = request.form['rotten_tomatoes']

        add_movie(title, release_date, language, genre, rotten_tomatoes)
        return redirect(url_for('get_all_movies_page'))
    else:
        return render_template('add_movie.html')

@app.route('/delete_movie', methods=['GET', 'POST'])
def delete_movie_route():
    if request.method == 'POST':
        title = request.form['delete_title']
        release_date = request.form['delete_release_date']

        deleted_count = delete_movie(title, release_date)
        if deleted_count == 0:
            error_message = "Movie not found."
            return render_template('error.html', error_message=error_message)

        return redirect(url_for('get_all_movies_page'))
    else:
        return render_template('delete_movie.html')


@app.route('/check_movie', methods=['GET', 'POST'])
def check_movie_route():
    if request.method == 'POST':
        update_title = request.form.get('update_title')
        movie = movies_collection.find_one({"Title": update_title})

        if movie:
            return render_template('update_movie_details.html', movie=movie)
        else:
            error_message = "Movie not found."
            return render_template('error.html', error_message=error_message)

    return render_template('check_movie.html')

@app.route('/update_movie_details/<old_title>', methods=['POST'])
def update_movie_details_route(old_title):
    movie = movies_collection.find_one({"Title": old_title})

    if request.method == 'POST':
        new_title = request.form['new_title']
        new_language = request.form['new_language']
        new_genre = request.form['new_genre']
        new_rotten_tomatoes = request.form['new_rotten_tomatoes']
        new_release_date = request.form['new_release_date']

        # Convert the new_release_date to a datetime object
        new_release_date = datetime.strptime(new_release_date, "%Y-%m-%d")

        new_data = {
            "Title": new_title,
            "Original_Language": new_language,
            "Genre": new_genre,
            "Rotten_Tomatoes": new_rotten_tomatoes,
        }

        # Update the movie with the new data and release date
        update_movie(old_title, movie['Release_Date'], new_data, new_release_date)
        return redirect(url_for('get_all_movies_page'))

    return render_template('update_movie_details.html', movie=movie)


@app.route('/search', methods=['GET', 'POST'])
def search_movie_route():
    if request.method == 'POST':
        search_title = request.form['search_title']
        movie = search_movie(search_title)
        return render_template('search_movie_result.html', movie=movie)
    else:
        return render_template('search_movie.html')

# Function to search for a movie in the database based on title
def search_movie(title):
    return movies_collection.find_one({"Title": title})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
