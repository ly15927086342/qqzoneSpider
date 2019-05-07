#coding = 'utf-8'
'''
模块功能：sqlite3数据库操作模块
作者：Li Yu
创建时间：2019/05/02
创建地点：武汉大学，湖北，武汉
作者邮箱：2014301610173@whu.edu.cn
'''

from tkinter import *
from tkinter import messagebox,filedialog
import sqlite3,os
from datetime import *

def createDB(sp_ins,dbname,curdir):
	if(dbname == ''):
		print(dbname)
		messagebox.showwarning('警告', '请输入数据库名称！')
	else:
		file = os.path.exists(curdir+'/db/'+dbname+'.db')
		print(curdir+'/db/'+dbname+'.db')
		print(file)
		if file: # 数据库已存在
			messagebox.showwarning('警告', '数据库已存在！')
			return
		createsql = '''
		create table qqzoneinfo
		(id integer primary key autoincrement,
		comment text,
		cmtnum int,
		likenum int,
		tid text,
		createtime long)
		'''
		conn = sqlite3.connect(curdir+'/db/'+dbname+'.db')
		c = conn.cursor()
		c.execute(createsql)
		conn.commit()
		conn.close()
		messagebox.showinfo('通知', '创建成功！')
		a = list(sp_ins.choosedb_cb['values'])
		a.append(dbname+'.db')
		sp_ins.dbchoose_cb['values'] = tuple(a)
		sp_ins.choosedb_cb['values'] = tuple(a)
		sp_ins.dbc_cb['values'] = tuple(a)

def chooseDB(db_ins,curdir):
	db_ins.filepath = filedialog.askopenfilename(initialdir= os.path.dirname(curdir+'/db/'),filetypes = (("DB files","*.db"),("all files","*.*")))
	db_ins.dbchoose_entry.select_clear()
	fp = StringVar()
	fp.set(db_ins.filepath)
	db_ins.dbchoose_entry.configure(textvariable=fp)

def getDBData(db_ins,dbname,tablename,curdir):
	if(dbname == ''):
		messagebox.showwarning('警告', '请选择数据库！')
		return
	conn = sqlite3.connect(curdir+'/db/'+dbname)
	c = conn.cursor()
	res = c.execute('select id,comment,cmtnum,likenum,tid,createtime from ' + tablename).fetchall()
	items = db_ins.dbtable_tree.get_children()
	[db_ins.dbtable_tree.delete(item) for item in items]
	i = 1
	print(len(res))
	for row in res:
		db_ins.dbtable_tree.insert("",END,text=str(i),values=(row[0],row[1],row[2],row[3],row[4],datetime.fromtimestamp(row[5])))
		i = i + 1
	conn.close()

def getData2Draw(dbname,tablename):
	data = []
	if(dbname == ''):
		messagebox.showwarning('警告', '请选择数据库！')
		return
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	res = c.execute('select * from ' + tablename).fetchall()
	for row in res:
		data.append([int(row[2]),int(row[3]),int(row[5]),row[1]]) # cmtnum,likenum,createtime,comment
	conn.close()
	return data

def deleteAll(db_ins,dbname,tablename):
	if(dbname == ''):
		return
	res = messagebox.askyesno('通知','确认清空？')
	print(res)
	if(res == False):
		return
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('delete from ' + tablename)
	conn.commit()
	conn.close()
	messagebox.showinfo('通知', '已清空！')

def choosePhantom(self,conf):
	conf.phfilepath = filedialog.askopenfilename(filetypes = (("phantomjs files","*.exe"),("all files","*.*")))
	self.phantomjs_entry.select_clear()
	fp = StringVar()
	fp.set(conf.phfilepath)
	self.phantomjs_entry.configure(textvariable=fp)
	with open(conf.curdir+'/db/phpos.txt','w') as f:
		f.write(conf.phfilepath)

def saveAccount(conf):
	with open(conf.curdir+'/db/account.txt','w') as f:
		f.write(conf.account)

def sqlopr(conn,cur,item,tablename):
	number = cur.execute("select * from "+tablename+" where tid = '"+item['tid']+"'").fetchall()
	if len(number) > 0:
		return
	cur.execute("insert into "+tablename+" (comment,cmtnum,tid,createtime) values (?,?,?,?)",(item['content'],int(item['cmtnum']),item['tid'],item['created_time']))
	conn.commit()