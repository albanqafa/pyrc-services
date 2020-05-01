#!/usr/bin/env python
import asyncio
import ssl
from datetime import datetime
import config

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
			self._raw(f'USER {config.ident.username} 0 * :{config.ident.realname}')
			self._raw('NICK ' + config.ident.nickname)
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
					elif 'REGISTER' in line:
						nickregistered_reg = False
						register_msg = line.split(' ')
						from_nick = line[line.find(':')+1 : line.find('!')]
						if len(register_msg) == 6: #if user actually sent a password
						
							with open('NickServ_db.csv', 'rt') as f:
								data = f.readlines()
							for line in data:
								if line.split(',')[1] == from_nick:
									nickregistered_reg = True
									self._raw('PRIVMSG ' + from_nick + ' :' + from_nick + ' is already registered')
									self._raw('PRIVMSG ' + from_nick + ' :to identify, please send an identify command like "/msg NickServ IDENTIFY ' + from_nick + 'password"')
							
							if nickregistered_reg == False:
								register_nick = from_nick
								register_passwd = register_msg[4]
								register_email = register_msg[5]
								f = open("NickServ_db.csv", "a")
								f.write('' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ',' + register_nick + ',' + register_passwd + ',' + register_email + '\n')
								f.close()
								self._raw('PRIVMSG ' + register_nick + ' :registered ' + register_nick + ' with password ' + register_passwd + ' and email ' + register_email)
						else:
							self._raw('PRIVMSG ' + from_nick + ' :something is wrong with your REGISTER message, you must include password and email')

					elif 'IDENTIFY' in line:
						nickregistered_ident = False
						nickidentified = False
						identify_msg = line.split(' ')
						from_nick = line[line.find(':')+1 : line.find('!')]
						if len(identify_msg) == 5: #if user actually sent a password
							identify_passwd = identify_msg[4] #password is in cell 4 of message sent
							print('user sent this password - ' + identify_passwd)
							with open('NickServ_db.csv', 'rt') as f:
								data = f.readlines()
							for line in data:
								if line.split(',')[1] == from_nick:
									print('Nick Registered')
									nickregistered_ident = True
									NickServ_db_line = line.split(',')
									NickServ_db_passwd = NickServ_db_line[2]
									print('saved password is ' + NickServ_db_passwd)
									if NickServ_db_passwd == identify_passwd:
										self._raw('PRIVMSG ' + from_nick + ' :you authenticated as ' + from_nick)
										self._raw('MODE #main +v ' + from_nick) #gives voice to user on channel #main
										nickidentified = True
									elif nickregistered_ident == True and nickidentified == False:
										self._raw('PRIVMSG ' + from_nick + ' :wrong password for ' + from_nick)
							if nickregistered_ident == False:
								self._raw('PRIVMSG ' + from_nick + ' :the nick ' + from_nick + ' is not currently registered.')
								self._raw('PRIVMSG ' + from_nick + ' :to register, please send a register command like "/msg NickServ REGISTER ' + from_nick + 'password email@domain.tld"')
								#dataLog.append(line)
							#print(dataLog)
						else:
							self._raw('PRIVMSG ' + from_nick + ' :something is wrong with your IDENTIFY message')

# Start
if __name__ == '__main__':
	Bot = IRC()
	asyncio.run(Bot._connect())
	while True: # Keep-alive loop, since we are asyncronous
		input('')
