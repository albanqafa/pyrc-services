#!/usr/bin/env python
import asyncio
import ssl
import os
import config
import time

def ssl_ctx():
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	if config.cert.file:
	    ctx.load_cert_chain(config.cert.file, password=config.cert.password)
	return ctx

class IRC:
	def __init__(self):
		self.options = {
			'host'       : config.connection.server,
			'port'       : config.connection.port,
			'limit'      : 1024,
			'ssl'        : ssl_ctx() if config.connection.ssl else None,
			'family'     : 10 if config.connection.ipv6 else 2,
			'local_addr' : (config.connection.vhost, 0) if config.connection.vhost else None
		}
		self.reader  = None
		self.writer  = None

	def _raw(self, data):
		self.writer.write(data[:510].encode('utf-8') + b'\r\n')

	async def _connect(self):
		try:
			self.reader, self.writer = await asyncio.open_connection(**self.options)
			self._raw(f'USER {config.ident_nowplaying.username} 0 * :{config.ident_nowplaying.realname}')
			self._raw('NICK ' + config.ident_nowplaying.nickname)
			oldtime = time.time()
		except Exception as ex:
			print(f'[!] - Failed to connect to IRC server! ({ex!s})')
		else:
			while not self.reader.at_eof():
				line = await self.reader.readline()
				if line:
					line = line.decode('utf-8').strip()
					print('[~] - ' + line)
					args = line.split()
					if args[0] == 'PING':
						self._raw('PONG ' + args[1][1:])
						print('PONG ' + args[1][1:])
					elif args[1] == '001':
						self._raw('JOIN ' + config.connection.channel)
					#elif 'test' in line:
					#	self._raw('PRIVMSG #main :IT WORKS')
					elif 'nowplaying' in line:
						print(oldtime)
						if time.time() - oldtime > 59:
							radio_stream = os.popen("curl -s https://some_live_radio_site/radio.html | head -n40 | tail -n1 | sed 's/<[^>]*>//g'")
							radio_playing = radio_stream.read()
							self._raw('PRIVMSG #main :' + radio_playing.replace('On Air','radio'))
							tv_stream = os.popen("curl -s https://some_live_video_site/test.html | sed 's/<[^>]*>//g'")
							tv_playing = tv_stream.read()
							self._raw('PRIVMSG #main :tv:    ' + tv_playing)
							oldtime = time.time()
						

# Start
if __name__ == '__main__':
	Bot = IRC()
	asyncio.run(Bot._connect())
	while True: # Keep-alive loop, since we are asyncronous
		input('')
