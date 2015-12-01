#!/usr/bin/env python

#http://www.rasterbar.com/products/libtorrent/manual.html
import libtorrent as lt
import time
import types
import sys
from subprocess import *
import threading

def xfrange(start, stop, step=1):
    while start < stop:
        yield start
        start += step

def printstatus():
	state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
	s = h.status()
	print('%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s\n' % (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state]))
	#if s.state == 4:
	#	break
	sys.stdout.flush()
	l = ''
	i = 0
	for p in s.pieces:
		if i >= piecestart and i <= pieceend:
			if p == True:
				l = l + '1'
			if p == False:
				l = l + '0'
		i = i+1
	print(l)

def addnewpieces():
	prio = h.piece_priorities()
	s = h.status()
	downloading = 0
	if len(s.pieces) == 0:
		return
	for piece in xfrange(piecestart, pieceend+1):
		if prio[piece] != 0 and s.pieces[piece]==False:
			downloading = downloading+1
	for piece in xfrange(piecestart,pieceend+1):
		if prio[piece] == 0 and downloading < piecesperite:
			print('downloading piece ',piece)
			h.piece_priority(piece,1)
			downloading = downloading+1
	for piece in xfrange(piecestart,pieceend+1):
		if prio[piece] != 0 and s.pieces[piece]==False:
			print('high prio ',piece)
			h.piece_priority(piece,7)
			break

cache = {}
def getpiece(i):
	global cache
	if i in cache:
		ret = cache[i]
		cache[i] = 0
		return ret
	while True:
		s = h.status()
		if len(s.pieces)==0:
			break
		if s.pieces[i]==True:
			break
		time.sleep(.1)
	h.read_piece(i)
	while True:
		#printstatus()
		#addnewpieces()
		piece = ses.pop_alert()
		if isinstance(piece, lt.read_piece_alert):
			if piece.piece == i:
				#sys.stdout.write(piece.buffer)
				return piece.buffer
			else:
				print('store somewhere')
				cache[piece.piece] = piece.buffer
			break
		time.sleep(.1)

completed = False
def writethread():
	global completed
	stream = 0
	for piece in xfrange(piecestart,pieceend+1):
		buf=getpiece(piece)
		if piece==piecestart:
			buf = buf[offset1:]
		if piece==pieceend:
			buf = buf[:offset2]
		print( 'output',piece,len(buf))
		if outputcmd=='-':
			stream = sys.stdout
		else:
			if stream == 0:
				stream = Popen(outputcmd.split(' '), stdin=PIPE).stdin
		try:
			stream.write(buf)
		except Exception as err:
			ses.remove_torrent(h)
			completed = True
			exit(0)
		time.sleep(.1)
	ses.remove_torrent(h)
	completed = True

def start(torrent,fileid,outdir,_outputcmd):
	global ses,h,piecestart,pieceend,offset1,offset2,piecesperite,outputcmd
	outputcmd=_outputcmd
	info = lt.torrent_info(torrent)
	piecesperite = 40*1024*1024/info.piece_length() # 40 MB
	print( 'piecesperite',piecesperite)
	print( 'info.piece_length()',info.piece_length())
	sizes = []
	i = 0
	for f in info.files():
		piecestart = int(f.offset/info.piece_length())
		pieceend = int((f.offset+f.size)/info.piece_length())
		sizes.append(f.size)
		print( i,f.path,f.size,f.offset,piecestart,pieceend)
		i=i+1
	if fileid == 'list':
		return
	if fileid == 'max':
		fileid = sizes.index(max(sizes))
	else:
		fileid = int(fileid)

	f = info.files()[fileid]
	print( f.path)
	piecestart = int(f.offset/info.piece_length())
	pieceend = int((f.offset+f.size)/info.piece_length())
	offset1 = f.offset%info.piece_length() #how many bytes need to be removed from the 1st piece
	offset2 = ((f.offset+f.size)%info.piece_length()) #how many bytes need we keep from the last piece
	print(piecestart,pieceend,offset1,offset2,info.piece_length())
	print((pieceend-piecestart+1)*info.piece_length()-(offset1+offset2),f.size)
	ses = lt.session()

	state = None
	#state = lt.bdecode(open(state_file, "rb").read())
	ses.start_dht(state)
	ses.add_dht_router("router.bittorrent.com", 6881)
	ses.add_dht_router("router.utorrent.com", 6881)
	ses.add_dht_router("router.bitcomet.com", 6881)

	ses.listen_on(6881, 6891)
	ses.set_alert_mask(lt.alert.category_t.storage_notification)
	h = ses.add_torrent({'ti': info, 'save_path': outdir})
	for i in range(info.num_pieces()):
		h.piece_priority(i,0)
	print('starting', h.name())
	for i in range(int(piecestart),int(piecestart+piecesperite)):
		if i <= pieceend:
			h.piece_priority(i,7)
			print('downloading piece '+str(i))
	threading.Thread(target=writethread).start()
	while not completed:
		printstatus()
		addnewpieces()
		time.sleep(1)

def main(torrent, outdir='/tmp'):
	torrent=sys.argv[1]
	fileid=0#'list'
	outputcmd='-'
	if len(sys.argv)>2:
		fileid=sys.argv[2]
	if len(sys.argv)>3:
		outdir=sys.argv[3]
	if len(sys.argv)>4:
		outputcmd=sys.argv[4]
	start(torrent,fileid,outdir,outputcmd)

if __name__ == "__main__":
    main()
