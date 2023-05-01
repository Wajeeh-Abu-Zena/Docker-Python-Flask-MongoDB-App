from base64 import b64encode
from flask import Flask, render_template, request
import TMDB_functions

app = Flask(__name__)

@app.route("/Hello")
def h():
    return 'Hello Team 6'

@app.route("/", methods=["POST", "GET"])
def home():
    # Read the image IDs from your database
    images = TMDB_functions.read_all_imgs()
    image_name = TMDB_functions.read_all_img_name()

    # Render the HTML template that displays the images
    return render_template('home.html', image_data=images)

@app.route("/search", methods=["POST", "GET"])
def search_movie():
    if request.method == 'POST':
        name = request.form['movie_name']
        image = TMDB_functions.search_movie(name)
        if image is None:
            return (f' The movie {name} not found 404' )
        else:
            return render_template('display_img.html', image=image)

@app.route("/add_img", methods=["POST"])
def add_img():
    if request.method == "POST":
        movie_name = request.form['movie']

        data = TMDB_functions.save_poster_to_mongodb(movie_name)
        image = b64encode(data.encode('utf-8')).decode("utf-8")
        return data

@app.route("/delete_img", methods=["POST"])
def delete_img():
    if request.method == "POST":
        movie_name = request.form['movie']
        name = TMDB_functions.delete_img_from_DB(movie_name)
        return f' The movie {name} was deleted successfully '

@app.route("/update_img", methods=["POST"])
def update_img():
    if request.method == "POST":
        old_value = request.form['old_value']
        new_name = request.form['new_value']
        res = TMDB_functions.update_img(old_value, new_name)
        return res

# run this command to run this application "docker run -p 3000:3000 poster_app"
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
