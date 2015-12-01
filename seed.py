#!/usr/bin/env python3

import yify
import db

def pickBestTorrent(torrents):
	result = False
	i = 0
	if isinstance(torrents, list):
		while (i < len(torrents)):
			if (result == False or torrents[i]['peers'] > result['peers']):
				result = torrents[i]
			i = i+1
	else:
		result = torrents
	return result

movies = []
p = 1
chunk = yify.listMovies(limit=50, page=1)
while (len(chunk) > 0):
	movies = movies + chunk
	p = p +1
	chunk = yify.listMovies(limit=50, page=p)
	db.addMovies(chunk)
