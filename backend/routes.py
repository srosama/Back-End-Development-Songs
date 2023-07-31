from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################


@app.route("/health", methods=["GET"])
def health():
    for _ in songs_list:      
        ...
        return {"status":"OK"}



@app.route("/count")
def count():
    if songs_list:
        return jsonify(length=len(songs_list)), 200

    return {"message": "Internal server error"}, 500

@app.route("/song")
def songs():
    collection = db["songs"]
    all_songs = collection.find({})

    songs_list = []
    for song in all_songs:
        # Convert the ObjectId to a string for serialization
        song["_id"] = str(song["_id"])
        songs_list.append(song)

    output = {"songs": songs_list}

    return jsonify(output)


@app.route('/song/<int:song_id>')
def get_song_by_id(song_id):
    findTheSong = db.songs.find_one({"id": song_id})
    if findTheSong is None:
        return {"message": "Song with the given ID not found"}, 404

    # Convert the ObjectId to a string for serialization
    findTheSong["_id"] = str(findTheSong["_id"])

    # Return the song as a JSON response
    return jsonify(findTheSong)
















@app.route("/song/<int:song_id>", methods=["POST"])
def create_song(song_id):
    # Check if a song with the given ID already exists
    findTheSong = db.songs.find_one({"id": song_id})
    if findTheSong:
        return jsonify({"Message": f"Song with id {song_id} already present"}), 302

    # Get the song data from the request body
    song_data = request.json
    if not song_data or "lyrics" not in song_data or "title" not in song_data:
        return jsonify({"Message": "Invalid song data"}), 400

    # Append the song data to the data list and insert it into the database
    song_data["id"] = song_id
    inserted_id = db.songs.insert_one(song_data)

    # Return a success response with the inserted ID
    return jsonify({"inserted id": str(inserted_id)}), 201



@app.route('/song/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    song_data = request.json
    if not song_data or "lyrics" not in song_data or "title" not in song_data:
        return jsonify({"message": "Invalid song data"}), 400

    # Find the song in the database
    existing_song = db.songs.find_one({"id": song_id})
    if existing_song:
        # Update the existing song with the new data
        update_result = db.songs.update_one({"id": song_id}, {"$set": song_data})
        if update_result.modified_count > 0:
            return jsonify({"message": f"Song with id {song_id} updated successfully"}), 200
        else:
            return jsonify({"message": f"Update for song with id {song_id} failed"}), 500
    else:
        return jsonify({"message": "Song not found"}), 404


@app.route('/song/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    existing_song = db.songs.find_one({"id": song_id})
    if existing_song:
        deleteTheSong = db.songs.delete_one()

