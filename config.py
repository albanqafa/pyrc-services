#!/usr/bin/env python
class connection:
	server  = '192.168.1.123'
	port    = 6667
	ipv6    = False
	ssl     = False
	vhost   = None
	channel = '#main'
	key     = None

class cert:
	file     = None
	password = None

class ident:
	nickname = 'NickServ'
	username = 'NickServ'
	realname = 'Nickname Service'

class login:
	nickserv = None
	operator = None
