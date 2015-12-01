#!/usr/bin/python

import json
import urllib.parse
import urllib.request
import urllib.parse

url="https://yify.is/index.php/api/v2/"
url_list="list_movies.json"
url_details="movie_details.json"

def request(url):
        try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})
                response = urllib.request.urlopen(req).read()
        except Exception as e:
                print(str(e))
                return False
        return json.loads(response.decode("utf-8"))

def getMovie(movieid):
        movie = request(url + url_details + '?movie_id=' + movieid)
        if movie is False:
                print("Error getting movie " + movieid)
        elif movie['status'] == 'error':
                print("Error getting movie " + movieid + ": " + movie['status_message'])
        else:
                return movie['data']

def listMovies(limit=30, page=1, sort_by='year', title=None):
        req_url = url + url_list + '?limit=' + str(limit) + '&page=' + str(page)
        if title is not None:
                req_url = req_url + '&query_term=' + urllib.parse.urlencode(title)
        movies = request(req_url)
        if movies is False or movies['status'] == 'error':
                print("Error getting movies")
        else:
                movies = movies['data']
                if 'movies' in movies.keys():
                        movies = movies['movies']
                        if (limit == 1):
                                movies = list(movies)
                else:
                        movies = []
                return movies


#movie = getMovie('117815')
#print(listMovies())
