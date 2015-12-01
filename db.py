#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('cache.db')
c = conn.cursor()

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

def addMovies(movies):
	sql = 'insert or ignore into movies values '
	for movie in movies:
		if movie is not None and 'torrents' in movie.keys():
			print('Adding ' + movie['title_long'])
			torrent = pickBestTorrent(movie['torrents'])
			if torrent is not False:
				v = '(' + movie['id'] + ',"' + movie['title'].strip() + '", ' + movie['year'] + ',' + torrent['size_bytes'] + ',"' + torrent['url'] + '"),'
				sql = sql + v
	sql = sql[:-1] + ';'
	c.execute(sql)
	conn.commit()

def getMovies():
	sql = 'select * from movies;'
	c.execute(sql)
	return c.fetchall()

def createTables():
	sql = 'create table if not exists movies (id int, name text, year int, size int, torrent text);'
	c.execute(sql)
	conn.commit()

def getMovie(title, year):
	sql = 'select * from movies where (name = \'' + title + '\') and (year = \'' + year + '\');'
	c.execute(sql)
	return c.fetchone()

createTables()

