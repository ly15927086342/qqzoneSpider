#coding = 'utf-8'
'''
模块功能：爬虫主模块，实现爬虫配置功能，爬虫GUI
作者：Li Yu
创建时间：2019/05/02
创建地点：武汉大学，湖北，武汉
作者邮箱：2014301610173@whu.edu.cn
'''

from tkinter import *
from tkinter import ttk,Listbox
from tkinter.ttk import *
from dbopr import *
from spider import *
from visualization import *
import os
from datetime import *

# 配置类
class Config(object):
	# 初始化
	def __init__(self):
		super(Config, self).__init__()
		self.curdir = os.getcwd() # 当前路径
		self.tablename = 'qqzoneinfo'
		self.phfilepath = ''
		self.account = ''
		self.password = ''
		self.refresh()

	# 更新配置
	def refresh(self):
		folder = os.path.exists(self.curdir+'/db/')
		if not folder: # 判断是否存在文件夹如果不存在则创建为文件夹
			os.makedirs(self.curdir+'/db/')
		# phfile = os.path.exists(self.curdir+'/db/phpos.txt') # 存phantomjs.exe的路径
		# if not phfile:
		# 	self.phfilepath = ''
		# else:
		# 	with open(self.curdir+'/db/phpos.txt','r') as f:
		# 		self.phfilepath = f.readline()
		self.phfilepath = self.curdir+'/phantomjs-2.1.1-windows/bin/phantomjs.exe'
		accountfile = os.path.exists(self.curdir+'/db/account.txt')
		if not accountfile:
			self.account = ''
		else:
			with open(self.curdir+'/db/account.txt','r') as f:
				self.account = f.readline()

# GUI类
class tkGUI(object):

	config = None # 配置类实例
	Spider = None # 爬虫类实例
	PaintChart = None # 可视化类实例

	# 界面初始化
	def __init__(self,conf):
		super(tkGUI, self).__init__()
		tkGUI.config = conf
		window = Tk()
		window.geometry('650x400')
		window.title('qqzoneSpider   | 注意：请合理使用爬虫，以防账号被封。“盗”亦有道 >_<')
		self.tab_control = ttk.Notebook(window)
		self.db_tab = ttk.Frame(self.tab_control)
		self.spider_tab = ttk.Frame(self.tab_control)
		self.visul_tab = ttk.Frame(self.tab_control)
		
		self.tab_control.add(self.db_tab, text='数据库')
		self.tab_control.add(self.spider_tab, text='爬虫')
		self.tab_control.add(self.visul_tab, text='可视化')

		self.dbs = []
		for filename in os.listdir(tkGUI.config.curdir+'/db/'):
			if(filename.split('.')[1] == 'db'):
				self.dbs.append(filename)

		self.db_init()
		self.spider_init()
		self.visul_init()

		self.tab_control.pack(expand=1, fill='both')
		window.mainloop()

	# 数据库界面初始化
	def db_init(self):
		self.dbname_lb = Label(self.db_tab, text= '数据库名',padx=10,pady=10,font=('微软雅黑'))
		self.dbname_entry = Entry(self.db_tab,width=30)
		self.dbname_btn = Button(self.db_tab,text='创建',command=lambda : createDB(self,self.dbname_entry.get(),tkGUI.config.curdir),bg="#BAE0E8",padx=10,)

		self.dbchoose_lb = Label(self.db_tab, text= '浏览数据库',padx=10,pady=10,font=('微软雅黑'))
		# self.dbchoose_entry = Entry(self.db_tab,width=30,state='disabled')
		column = ('id','comment','cmtnum','likenum','tid','createtime')
		self.dbtable_tree = ttk.Treeview(self.db_tab,columns = column,show='headings')
		self.dbtable_tree.column('id',width=30)
		self.dbtable_tree.column('comment',width=200)
		self.dbtable_tree.column('cmtnum',width=50)
		self.dbtable_tree.column('likenum',width=50)
		self.dbtable_tree.column('tid',width=100)
		self.dbtable_tree.column('createtime',width=100)
		self.dbtable_tree.heading('id',text='id')
		self.dbtable_tree.heading('comment',text='内容')
		self.dbtable_tree.heading('cmtnum',text='评论数')
		self.dbtable_tree.heading('likenum',text='点赞数')
		self.dbtable_tree.heading('tid',text='tid')
		self.dbtable_tree.heading('createtime',text='发表时间')

		self.dbchoose_cb = Combobox(self.db_tab,values=self.dbs)
		if(len(self.dbs) > 0):
			self.dbchoose_cb.current(0)

		# self.dbchoose_btn = Button(self.db_tab,text='选择',command=lambda : chooseDB(self,tkGUI.config.curdir),bg="#BAE0E8",padx=10,)
		self.dbwatch_btn = Button(self.db_tab,text='查看',command=lambda : getDBData(self,self.dbchoose_cb.get(),tkGUI.config.tablename,tkGUI.config.curdir),bg="#BAE0E8",padx=10,)
		self.dbdelete_btn = Button(self.db_tab,text='清空',command=lambda : deleteAll(self,self.dbchoose_cb.get(),tkGUI.config.tablename),bg='#BAE0E8',padx=10)

		self.dbname_lb.grid(column=0, row=0,sticky=W)
		self.dbname_entry.grid(column=1,row=0,sticky=W+E)
		self.dbname_btn.grid(column=2,row=0)

		self.dbchoose_lb.grid(column=0,row=1,sticky=W)
		self.dbchoose_cb.grid(column=1,row=1,sticky=W+E)
		# self.dbchoose_btn.grid(column=2,row=1,padx=10)
		self.dbwatch_btn.grid(column=2,row=1,padx=10)	
		self.dbdelete_btn.grid(column=3,row=1,padx=10)
		self.dbtable_tree.grid(column=0,row=2,columnspan=4,sticky=E+W,padx=10)

	# 爬虫界面初始化
	def spider_init(self):
		tkGUI.Spider = QQzoneSpider()
		ph = StringVar()
		ph.set(tkGUI.config.phfilepath)
		ac = StringVar()
		ac.set(tkGUI.config.account)
		

		# self.phantomjs_lb = Label(self.spider_tab, text= 'phantomjs位置',padx=10,pady=10,font=('微软雅黑'))
		# self.phantomjs_entry = Entry(self.spider_tab,width=30,state='disabled',textvariable=ph)
		# self.phantomjs_btn = Button(self.spider_tab,text='选择',command=lambda : choosePhantom(self,tkGUI.config),bg="#BAE0E8",padx=10,)

		self.choosedb_lb = Label(self.spider_tab,text="选择数据库",padx=10,pady=10,font=('微软雅黑'))
		self.choosedb_cb = Combobox(self.spider_tab,values=self.dbs)
		if(len(self.dbs) > 0):
			self.choosedb_cb.current(0)

		self.account_lb = Label(self.spider_tab, text= '你的账号',padx=10,pady=10,font=('微软雅黑'))
		self.account_entry = Entry(self.spider_tab,width=30,textvariable=ac)
		self.password_lb = Label(self.spider_tab, text= '你的密码',padx=10,pady=10,font=('微软雅黑'))
		self.password_entry = Entry(self.spider_tab,width=30,show="*")
		self.target_lb = Label(self.spider_tab,text='好友账号',padx=10,pady=10,font=('微软雅黑'))
		self.target_entry = Entry(self.spider_tab,width=30)
		self.spider_btn = Button(self.spider_tab,text="S1爬取说说",command=lambda : tkGUI.Spider.startSpider(self,tkGUI.config,self.account_entry.get(),self.password_entry.get(),self.choosedb_cb.get(),self.target_entry.get()),bg="#BAE0E8",padx=10)
		self.spider_like_btn = Button(self.spider_tab,text="S2爬取点赞数",command=lambda : tkGUI.Spider.likeNumSpider(self,tkGUI.config,self.account_entry.get(),self.password_entry.get(),self.choosedb_cb.get(),self.target_entry.get()),bg="#BAE0E8",padx=10)
		self.spider_pb = Progressbar(self.spider_tab)
		self.spider_load = Label(self.spider_tab,text = '未开始',padx=10,pady=10)

		# self.spider_like_btn['state'] = 'normal'
		# self.phantomjs_lb.grid(column=0, row=0,sticky=W)
		# self.phantomjs_entry.grid(column=1,row=0,padx=10)
		# self.phantomjs_btn.grid(column=2,row=0,padx=10,sticky=W)

		self.choosedb_lb.grid(column=0, row=1,sticky=W)
		self.choosedb_cb.grid(column=1,row=1,sticky=W+E,padx=10)

		self.account_lb.grid(column=0,row=2,sticky=W)
		self.account_entry.grid(column=1,row=2)
		self.password_lb.grid(column=0,row=3,sticky=W)
		self.password_entry.grid(column=1,row=3,padx=10)
		self.target_lb.grid(column=0,row=4,sticky=W)
		self.target_entry.grid(column=1,row=4,padx=10)
		self.spider_btn.grid(column=2,row=4,sticky=E,padx=10)
		self.spider_like_btn.grid(column=3,row=4,sticky=E,padx=10)
		self.spider_pb.grid(column=0,row=5,columnspan=2,sticky=E+W,pady=0,padx=10)
		self.spider_load.grid(column=2,row=5,sticky=W)

	# 可视化界面初始化
	def visul_init(self):
		self.img_scatter = PhotoImage(file = 'img/fsux_scatter.png')
		self.img_bar = PhotoImage(file = 'img/fsux_bar.png')
		self.img_pie = PhotoImage(file = 'img/fsux_pie.png')
		self.img_heatmap = PhotoImage(file = 'img/fsux_heatmap.png')
		self.img_wordcloud = PhotoImage(file = 'img/fsux_wordcloud.png')
		self.img_regression = PhotoImage(file = 'img/fsux_regression.png')

		tkGUI.PaintChart = PaintChart()

		self.dbc_lb = Label(self.visul_tab,text='选择数据源',padx=10,pady=10,font=('微软雅黑'))
		self.dbc_cb = Combobox(self.visul_tab,values=self.dbs)
		if(len(self.dbs) > 0):
			self.dbc_cb.current(0)
		self.intro_lb = Label(self.visul_tab,text='点击以下按钮，获得分析图。热力图在右侧输入年份',padx=10,pady=10,font=('微软雅黑'))
		self.year_entry = Entry(self.visul_tab)
		self.btn_bar = Label(self.visul_tab)
		self.scatter_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,1),image = self.img_scatter,padx=10,pady=10,width=75,height=75)
		self.scatter3d_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,0),image = self.img_scatter,padx=10,pady=10,width=75,height=75)
		self.bar_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,3),image = self.img_bar,padx=10,pady=10,width=75,height=75)
		self.pie_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,4),image = self.img_pie,padx=10,pady=10,width=75,height=75)
		self.heatmap_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,5),image = self.img_heatmap,padx=10,pady=10,width=75,height=75)
		self.wordcloud_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,6),image = self.img_wordcloud,padx=10,pady=10,width=75,height=75)
		self.regression_btn = Button(self.btn_bar,command=lambda:tkGUI.PaintChart.Draw(self,tkGUI.config.curdir,self.dbc_cb.get(),tkGUI.config.tablename,2),image = self.img_regression,padx=10,pady=10,width=75,height=75)
		self.scatter_lb = Label(self.btn_bar,text='散点图(二维)')
		self.scatter3d_lb = Label(self.btn_bar,text='散点图(三维)')
		self.bar_lb = Label(self.btn_bar,text='柱状图')
		self.pie_lb = Label(self.btn_bar,text='南丁玫瑰图')
		self.heatmap_lb = Label(self.btn_bar,text='热力图')
		self.wordcloud_lb = Label(self.btn_bar,text='词云')
		self.regression_lb = Label(self.btn_bar,text='回归曲线')
		self.analysis_pb = Progressbar(self.visul_tab)
		self.analysis_lb = Label(self.visul_tab,text='未开始')

		self.dbc_lb.grid(column=0,row=0,sticky=W)
		self.dbc_cb.grid(column=1,row=0,sticky=W+E,padx=10)
		self.intro_lb.grid(column=0,row=1,sticky=W)
		self.year_entry.grid(column=1,row=1,sticky=E+W,padx=10)
		self.btn_bar.grid(column=0,columnspan=2,row=2)
		self.scatter_btn.grid(column=0,row=0,padx=5,pady=10)
		self.scatter3d_btn.grid(column=1,row=0,padx=5,pady=10)
		self.bar_btn.grid(column=2,row=0,padx=5,pady=10)
		self.pie_btn.grid(column=3,row=0,padx=5,pady=10)
		self.heatmap_btn.grid(column=4,row=0,padx=5,pady=10)
		self.wordcloud_btn.grid(column=5,row=0,padx=5,pady=10)
		self.regression_btn.grid(column=0,row=2,padx=5,pady=10)
		self.scatter_lb.grid(column=0,row=1)
		self.scatter3d_lb.grid(column=1,row=1)
		self.bar_lb.grid(column=2,row=1)
		self.pie_lb.grid(column=3,row=1)
		self.heatmap_lb.grid(column=4,row=1)
		self.wordcloud_lb.grid(column=5,row=1)
		self.regression_lb.grid(column=0,row=3)
		self.analysis_pb.grid(column=0,row=3,padx=10,pady=0,sticky=E+W)
		self.analysis_lb.grid(column=1,row=3,padx=10,pady=0,sticky=W)

# 主程序入口
if __name__ == '__main__':
	conf = Config() # 配置
	app = tkGUI(conf) # 启动界面

	