import base64
from io import BytesIO
import requests
from pymongo import MongoClient
from gridfs import GridFS, GridFSBucket
from config_file import Config

CONFIG_PATTERN = 'http://api.themoviedb.org/3/configuration?api_key={key}'
IMG_PATTERN = 'http://api.themoviedb.org/3/movie/{imdbid}/images?api_key={key}'
KEY = Config.TMDB_API_KEY

# connect to the mongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['mov_img']
fs = GridFS(db)
bucket = GridFSBucket(db)

def search_movie(movie_name):
    # search for the file by Name
    img = fs.find_one({"filename": f"{movie_name}.jpeg"})
    # check if the file was found
    print(img)
    if img is None:
        return None
    else:
        img_io = BytesIO(img.read())
        encode_img = base64.b64encode(img_io.getvalue())
        image = encode_img.decode('utf-8')
        return image

def read_all_imgs():
    metadata_docs = bucket.find()
    if metadata_docs is None:
        return 'File not found', 404

    images = []
    for img_id in metadata_docs:
        img_io = BytesIO(img_id.read())
        encode_img = base64.b64encode(img_io.getvalue())
        images.append(encode_img.decode('utf-8'))
    return images

def read_all_img_name():
    metadata_docs = db.fs.files.find()

    for n in metadata_docs:
        filename = n['filename']
        print(filename)

def delete_img_from_DB(movie_name):
    try:
        existing_file = fs.find_one({"filename": f"{movie_name}.jpeg"})
        if existing_file:

            # Delete the file
            res = fs.delete(existing_file._id)
            return movie_name

        else:
            return f'No Movie image "{movie_name}" found with the specified filename'

    except Exception as e:
        print(f'An error occurred: {e}')

def update_img(old_value, new_value):
    img_name = fs.find_one({"filename": f"{old_value}.jpeg"})
    if img_name:
        # update the value in MongoDB
        fs.update(
            {'_id': img_name.file_id},
            {'$set': {'content': new_value.encode()}}
        )
    return 'updated'

def _get_json(url):
    r = requests.get(url)
    return r.json()
def get_first_poster_url(imdbid):
    config = _get_json(CONFIG_PATTERN.format(key=KEY))
    base_url = config['images']['base_url']
    sizes = config['images']['poster_sizes']

    def size_str_to_int(x):
        return float("inf") if x == 'original' else int(x[1:])

    max_size = max(sizes, key=size_str_to_int)
    posters = _get_json(IMG_PATTERN.format(key=KEY, imdbid=imdbid))['posters']
    if posters:
        rel_path = posters[0]['file_path']
        url = "{0}{1}{2}".format(base_url, max_size, rel_path)
        return url

def save_poster_to_mongodb(movie_name):

    # Query TMDB API to get movie ID and poster URL
    search_url = f'http://api.themoviedb.org/3/search/movie?api_key={KEY}&query={movie_name}'
    search_results = _get_json(search_url)['results']
    if not search_results:
        return f"No movies found for '{movie_name}'"
    imdbid = search_results[0]['id']
    url = get_first_poster_url(imdbid)
    if not url:
        return f"No posters found for '{movie_name}'"

    # check if poster image already exists in database
    existing_file = fs.find_one({"filename": f"{movie_name}.jpeg"})
    if existing_file:
        return f"Poster image for '{movie_name}' already exists in MongoDB with ID '{existing_file._id}'"

    # Download and save the poster image
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return f"Failed to download poster image for '{movie_name}'"

        poster_id = fs.put(r.content, filename=f"{movie_name}.jpeg", content_type="image/jpeg")
        res = (f"Saved poster image for '{movie_name}' with ID '{poster_id}' to MongoDB")
        return res
    except:
        return f"Failed to save poster image for '{movie_name}' to MongoDB"



if __name__ == "__main__":
    #movie_name = input("Enter the name of the movie: ")
    #save_poster_to_mongodb(movie_name)
    search_movie('A')


