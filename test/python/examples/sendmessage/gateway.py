#--coding:utf-8--

"""

gateway 接入client，对client的请求进行处理，并将其转发到内部的server处理

server反向调用client的实现：
 1. client 登录到gateway时，提交client的uid，gateway将uid与client的连接绑定
 2. server发起反向调用时，创建client的代理，并将client的uid添加到调用参数的extra
 3. server的请求是通过mq传递到gateway，gateway解析出client的uid，找到对应的client的connection，并通过此connection发送rpc消息到client

gateway支持socket,websocket方式接入,同时只能一种方式,启动参数(gwserver/gwserver_ws)区分两种接入方式( services.xml定义了两个gws服务器)


"""

import os,os.path,sys,struct,time,traceback,signal,string
import tcelib as tce
import uuid,copy
from sns import *
import gevent
import gevent.monkey
gevent.monkey.patch_all()

USER_ID = 100

class EventListener(tce.RpcConnectionEventListener):
	def __init__(self,server):
		tce.RpcConnectionEventListener.__init__(self)
		self.server = server



	def onDataPacket(self, conn, m):
		'''
			接收到第一个消息包进行检测
				1.检查token是否合法
				2.检查device_id与token是否是同一台设备发出
				3.如果不一致，返回错误信息，通过ITermnial.onNotifyMessage()传递到前端设备
			@return:
				False - tce将关闭connection
				True - okay
		'''
		if conn.getRecvedMessageCount() == 1:
			user_id = m.extra.getValue('__token__')
			if not user_id:
				print '__token__ not be set,reject!'
				return False
			conn.setUserId( user_id )
			self.server.onUserOnline(user_id)
		return True

	def onDisconnected(self, conn):
		tce.RpcConnectionEventListener.onDisconnected(self, conn)
		print 'onDisconnected..'
		userid = conn.getUserId()
		if userid:
			self.server.onUserOffline(userid)

	def onConnected(self, conn):
		print 'onConnected..'




class TerminalGatewayServer(ITerminalGatewayServer):
	def __init__(self):
		ITerminalGatewayServer.__init__(self)

		self.listener = EventListener(self)
		tce.RpcCommunicator.instance().setConnectionEventListener(self.listener)
		self.prxServer = IMessageServerPrx.createWithEpName('mq_server')


	def onUserOnline(self,user_id):
		name = tce.currentServer().getName()
		self.prxServer.onUserOnLine_oneway(user_id,name)

	def onUserOffline(self,user_id):
		name = tce.currentServer().getName()
		self.prxServer.onUserOffLine_oneway(user_id,name)

	def ping(self,ctx):
		print 'ping..'


def usage():
	print 'usage: python gwserver.py gwserver | gwserver_ws'

def main():
	argv = copy.deepcopy(sys.argv)
	name = 'gwserver'
	if len(sys.argv) > 1:
		name = sys.argv[-1]

	if not name  in ('gwserver','gwserver_ws'):
		usage()
		sys.exit()

	print 'server name is: ',name

	cfg =''
	eps_listen=[]
	loopbacks=[]
	try:
		while argv:
			p = argv.pop(0).strip().lower()
			if p =='-name':
				name = argv.pop(0)
			if p=='-config':
				cfg = argv.pop(0)

		tce.RpcCommunicator.instance().init( name ).initMessageRoute('./services.xml')
		server = tce.RpcCommunicator.instance().currentServer()
		value = server.getPropertyValue('listen')
		eps_listen = value.split(',')

		value = server.getPropertyValue('loopback')
		pairs = value.split(',')
		for p in pairs:
			call,return_ = p.split('#')
			loopbacks.append( (call,return_) )

	except:
		traceback.print_exc()
		return

	if  not eps_listen:
		return


	servant = TerminalGatewayServer()

	for ep in eps_listen:
		ep = ep.strip()
		id = uuid.uuid4().hex
		adapter = tce.RpcCommunicator.instance().createAdapter(id,ep)
		adapter.addServant(servant)

	for lpb in loopbacks:
		lpb = map(string.strip,lpb)
		call,back = lpb
		ep1 = tce.RpcCommunicator.instance().currentServer().findEndPointByName(call)
		ep2 = tce.RpcCommunicator.instance().currentServer().findEndPointByName(back)
		if not ep1 or not ep2:
			print 'error: loopback items <%s> not found!'%str(lpb)
			return -1
		if ep1.type not in ('mq','qpid')  or ep2.type not in ('mq','qpid'):
			print 'error: loopback items <%s> must be mq type!'%str(lpb)
			return -1
		ep1.impl.setLoopbackMQ(ep2.impl)

	print 'TerminalGatewayServer:',name,' Started! \nWaiting for shutdown..'
	tce.RpcCommunicator.instance().waitForShutdown()

if __name__ == '__main__':
	sys.exit( main())