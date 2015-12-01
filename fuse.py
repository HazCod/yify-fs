#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno

import yify
import time
import stat

from acdfuse import FUSE, FuseOSError, Operations
import db
import libtorrent
import tempfile
import btcat

import threading

from urllib.request import Request, urlopen


class Passthrough(Operations):
    def __init__(self, root):
        self.root = root
        self.dir = tempfile.mkdtemp()
        print("Using " + self.dir)

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print('access() : ' + path)


    def chmod(self, path, mode):
        return False

    def chown(self, path, uid, gid):
        return False

    def isMediaFile(self, path):
        return ((path.startswith('/movies') and len(path.split('/'))) == 4) or (path.startswith('/series') and len(path.split('/')) == 5)

    def getattr(self, path, fh=None):
        print('getattr : ' + path)
        now = time.time()
        st = {}
        # mode decides access permissions and if file object is a directory (stat.S_IFDIR), file (stat.S_IFREG) or a special file
        if self.isMediaFile(path):
            st['st_mode'] = stat.S_IFREG
        else:
            st['st_mode']   = stat.S_IFDIR
        st['st_ino']    = 0
        st['st_dev']    = 0
        st['st_nlink']  = 1
        st['st_uid']    = os.getuid() #file object's user id
        st['st_gid']    = os.getgid() #file object's group id
        st['st_size']   = 0    #size in bytes
        st['st_atime']  = now  #last access time in seconds
        st['st_mtime']  = now  #last modified time in seconds
        st['st_ctime']  = now
        #st_blocks is the amount of blocks of the file object, and depends on the block size of the file system (here: 512 Bytes)
        st['st_blocks'] = (int) ((st['st_size'] + 511) / 512)
        return st

    def readdir(self, path, fh):
        print('readdir : ' + path)
        dirents = ['.', '..']
        if (path == '/'):
            dirents = dirents + ['movies', 'series']
        elif path.startswith('/movies'):
            depth = len(path.split('/'))
            if depth == 2:
                for m in db.getMovies():
                    dirents.append(m[1] + ' (' + str(m[2]) + ')')
            elif depth == 3:
                moviename = path.split('/')[2].split('(')[0].strip()
                print('Showing movie ' + moviename)
                dirents = dirents + [moviename + '.mp4']
            else:
                pass
        else:
            print('readdir() : path nonexistant: ' + path)
        return dirents

    def readlink(self, path):
        return False

    def mknod(self, path, mode, dev):
        return False #os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        return False

    def mkdir(self, path, mode):
        return False

    def statfs(self, path):
        print('statfs() : ' + path)
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return False #os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return False #os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return False #os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return False #os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return False #os.utime(self._full_path(path), times)

    # File methods
    # ============

    def download(self, url, dest):
        print("DL " + url + " -> " + dest)
        q = Request(url)
        q.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
        a = urlopen(q).read()
        with open(dest, 'wb') as f:
            f.write(a)

    def open(self, path, flags):
        print('open() : ' + path)
        #if isMovie..
        moviename = os.path.splitext(os.path.basename(path))[0]
        movieyear = path.split('/')[2]
        movieyear = movieyear[movieyear.index('(')+1 : movieyear.index(')')]
        print("Year: " + movieyear)
        print("Looking for " + moviename)
        movie = db.getMovie(moviename, movieyear)
        if movie is not None:
            print("Downloading torrent from " + movie[4] + " to " + self.dir + '/' + moviename + '.torrent')
            try:
                self.download(movie[4], self.dir + '/' + moviename + '.torrent')
            except Exception as e:
                print('Could not download torrent file: ' + str(e))
            print("Torrent file downloaded to " + self.dir + '/' + moviename + '.torrent')
            print("Downloading commencing")
            threading.Thread(target=btcat.main(self.dir + '/' + moviename + '.torrent', self.dir)).start()
        else:
            print("Could not find " + path)

    def create(self, path, mode, fi=None):
        return False

    def read(self, path, length, offset, fh):
        print('read() : ' + path + ' , length ' + str(length) + ', offset ' + offset)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        return False

    def truncate(self, path, length, fh=None):
        print('truncate : ' + length)
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        print('flush')
        return False

    def release(self, path, fh):
        print('release')
        return False

    def fsync(self, path, fdatasync, fh):
        print('fsync')
        return False


def main(m):
    FUSE(Passthrough(False), m, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1])