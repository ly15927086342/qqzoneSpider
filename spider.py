#coding = 'utf-8'
'''
模块功能：爬取QQ空间的说说内容、评论数、发表时间、点赞数、tid
作者：Li Yu
创建时间：2019/05/04
创建地点：武汉大学，湖北，武汉
作者邮箱：2014301610173@whu.edu.cn
'''

from tkinter import messagebox,filedialog
from tkinter.ttk import Progressbar
from dbopr  import *
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
import json
import sqlite3
import re
import time
import random
import threading

headers={
	# 'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
	'User-Agent':'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)'
}

# 爬虫类
class QQzoneSpider(object):
	# 初始化
	def __init__(self):
		super(QQzoneSpider, self).__init__()
		self.cookie,self.g_tk,self.qzonetoken = '','',''
	
	# 加密获取g_tk参数
	def get_g_tk(self,cookie):
	    hashes = 5381
	    for letter in cookie['p_skey']:
	        hashes += (hashes << 5) + ord(letter)  # ord()是用来返回字符的ascii码
	    return hashes & 0x7fffffff

	# 模拟登陆
	def start_login(self,conf):
		# desired_cap = DesiredCapabilities.PHANTOMJS.copy()
		# 修改请求头中的UA
		# desired_cap['phantomjs.page.settings.userAgent'] = headers['User-Agent']
		# driver = webdriver.PhantomJS(executable_path = conf.phfilepath,desired_capabilities=desired_cap)
		driver = webdriver.PhantomJS(executable_path = conf.phfilepath)
		#driver = webdriver.Chrome(executable_path = "E:\\phantomjs-2.1.1-windows\\bin\\chromedriver.exe")
		url = "https://qzone.qq.com/"
		# url = 'https://www.baidu.com/'
		driver.set_page_load_timeout(15)# 15秒超时
		driver.set_script_timeout(15)
		try:
			driver.get(url)
			driver.switch_to.frame('login_frame')
			driver.find_element_by_id('switcher_plogin').click()

			driver.find_element_by_id('u').clear()
			driver.find_element_by_id('u').send_keys(conf.account)  
			driver.find_element_by_id('p').clear()
			driver.find_element_by_id('p').send_keys(conf.password)  

			driver.find_element_by_id('login_button').click()

			time.sleep(3)

			html = driver.page_source
			g_qzonetoken = re.search('window\.g_qzonetoken = \(function\(\)\{ try\{return (.*?);\} catch\(e\)',html)
			if(g_qzonetoken == None):
				messagebox.showerror('错误', '登陆失败！')
				return '','','','fai'
			qzonetoken = str(g_qzonetoken[0]).split('\"')[1]

			cookie_list = driver.get_cookies()
			cookie_dict = {}

			for cookie in cookie_list:
				cookie_dict[cookie['name']]=cookie['value']

			g_tk = self.get_g_tk(cookie_dict)

			return cookie_dict,g_tk,qzonetoken,'suc'
		except:
			messagebox.showerror('错误', '登陆超时！可能被封，请在浏览器中访问空间进行确认。如果被封，请等解封后再爬取。')
			self.tk_ins.spider_load.configure(text = '失败')

	# 爬取说说
	def spidercmt(self):
		if(self.cookie == ''):# 未登陆
			self.cookie,self.g_tk,self.qzonetoken,state = self.start_login(self.conf)
			if(state == 'fai'):
				self.tk_ins.spider_load.configure(text = '失败')
				return

		# print(cookie)
		# print(g_tk)
		# print(qzonetoken)

		conn = sqlite3.connect(self.conf.curdir+'/db/'+self.dbname)
		cur = conn.cursor()

		sessions = requests.session()

		total = 1
		hassp = 0
		while hassp < total:
			param = {
				'uin': self.target,
	            'ftype': '0',
	            'sort': '0',
	            'pos': hassp,
	            'num': '20',
	            'replynum': '100',
	            'g_tk': [self.g_tk, self.g_tk],
	            'callback': '_preloadCallback',
	            'code_version': '1',
	            'format': 'jsonp',
	            'need_private_comment': '1',
	            'qzonetoken': self.qzonetoken
			}
			respond = sessions.get('https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',params=param,headers=headers,cookies=self.cookie,timeout=10)
			# print(respond.text)

			'''_preloadCallback({"cginame":2,"code":-10031,"logininfo":{"name":"Mr. Green","uin":952700304},"message":"对不起,主人设置了保密,您没有权限查看","name":"Mr. Green","right":2,"smoothpolicy":{"comsw.disable_soso_search":0,"l1sw.read_first_cache_only":0,"l2sw.dont_get_reply_cmt":0,"l2sw.mixsvr_frdnum_per_time":50,"l3sw.hide_reply_cmt":0,"l4sw.read_tdb_only":0,"l5sw.read_cache_only":0},"subcode":2,"usrinfo":{"concern":0,"createTime":"","fans":0,"followed":0,"msg":"","msgnum":0,"name":"933220560","uin":933220560}});'''
			# return
			r = re.sub("_preloadCallback","",respond.text)
			test = r[1:-2]
			Data = json.loads(test)

			if(Data['code'] == -10031):
				messagebox.showwarning('警告', '您没有权限查看该空间！')
				self.tk_ins.spider_pb['value'] = 0
				self.tk_ins.spider_load.configure(text = '失败')
				return

			#msg = []

			if not re.search('lbs',test):
				self.tk_ins.spider_pb['value'] = 100
				self.tk_ins.spider_load.configure(text = '下载完成')
				break
			else:
				# print(Data['msglist'])
				if(hassp == 0):
					total = int(Data['total'])
				hassp = hassp + len(Data['msglist'])
				self.tk_ins.spider_pb['value'] =  100 * hassp / total 
				self.tk_ins.spider_load.configure(text = str(hassp)+'/'+str(total))
				for j in range(len(Data['msglist'])):
					#msg.append(Data['msglist'][j])
					sqlopr(conn,cur,Data['msglist'][j],self.conf.tablename)
			time.sleep(2)
			print("pos {0} suc".format(hassp))
		self.tk_ins.spider_pb['value'] = 100
		self.tk_ins.spider_load.configure(text = '完毕')
		conn.close()
		#print(cookie_dict)
		#print(json.dumps(msg[0],indent=4,ensure_ascii=False))
		#print(msg[0])

	# 爬取点赞数
	def spiderlikenum(self):
		if(self.cookie == ''):# 未登陆
			self.cookie,self.g_tk,self.qzonetoken,state = self.start_login(self.conf)
			if(state == 'fai'):
				self.tk_ins.spider_load.configure(text = '失败')
				return

		conn = sqlite3.connect(self.conf.curdir+'/db/'+self.dbname)
		cur = conn.cursor()

		sessions = requests.session()
		count = len(cur.execute('select * from '+self.conf.tablename+' where likenum is Null').fetchall())
		total = count

		url = 'http://user.qzone.qq.com/'+self.target+'/mood/'

		while count != 0:
			ress = cur.execute('select * from '+self.conf.tablename+' where likenum is Null').fetchall()
			count = len(ress)-1
			idc = ress[0][0]
			tid = ress[0][4]
			#res = cur.execute('select tid from qqzoneinfo where id='+str(i)).fetchall()
			#tid = res[0][0]
			_stp = int(round(time.time() * 1000)) #时间戳
			param = {
		    	'_stp': str(_stp),
		    	'unikey': url + tid + '.1<.>' + url + '.1',
		    	'g_tk': [self.g_tk, self.g_tk],
		    	'face': '0',
		    	'fupdate': '1',
		    	'qzonetoken': self.qzonetoken
		    }

			respond = sessions.get('https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2',params=param,headers=headers,cookies=self.cookie,timeout=10)
			r = re.sub("_Callback","",respond.text)
			#print(r)
			test = r[1:-2]
			if test == None or test == "" or len(test) == 0:
				print("lose data")
				continue
			else:
				try:
					Data = json.loads(test)
					likenum = Data['data'][0]['current']['likedata']['cnt']
					cur.execute("update "+self.conf.tablename+" set likenum = "+str(likenum)+" where id = "+str(idc))
					conn.commit()
					self.tk_ins.spider_pb['value'] =  100 * (total-count) / total 
					self.tk_ins.spider_load.configure(text = str(total-count)+'/'+str(total))
					print('like:'+str(likenum))
					print(idc)
					ran = random.random()
					time.sleep(1+ran)
				except:
					print("error")
		self.tk_ins.spider_pb['value'] =  100
		self.tk_ins.spider_load.configure(text = '完毕')
		conn.close()

	# 启动线程爬取说说
	def startSpider(self,sp_ins,conf,account,password,dbname,target):
		sp_ins.spider_load.configure(text='爬虫准备...')
		sp_ins.spider_pb['value'] =  0

		conf.account = account
		conf.password = password
		saveAccount(conf)
		# 爬取所有说说
		# thread.start_new_thread(spidercmt,(sp_ins,conf,dbname))
		self.tk_ins = sp_ins
		self.conf = conf
		self.account = account
		self.password = password
		self.dbname = dbname
		self.target = target

		th1 = threading.Thread(target=self.spidercmt, args=())
		th1.start()
		# spidercmt(sp_ins,conf,dbname)

	# 启动线程爬取点赞数
	def likeNumSpider(self,sp_ins,conf,account,password,dbname,target):
		sp_ins.spider_load.configure(text='爬虫准备...')
		sp_ins.spider_pb['value'] =  0

		conf.account = account
		conf.password = password
		saveAccount(conf)
		# 爬取所有点赞数
		# thread.start_new_thread(spidercmt,(sp_ins,conf,dbname))
		self.tk_ins = sp_ins
		self.conf = conf
		self.account = account
		self.password = password
		self.dbname = dbname
		self.target = target

		th2 = threading.Thread(target=self.spiderlikenum, args=())
		th2.start()


