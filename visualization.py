#coding = 'utf-8'
'''
模块功能：利用pyecharts 0.5版本（旧版）进行空间数据的可视化分析初
		 版包括二维散点图、三维散点图、一元线性回归分析（点赞数和评
		 论数）、词云、热力图、柱状图、南丁玫瑰图，后续可能会更新
作者：Li Yu
创建时间：2019/05/04
创建地点：武汉大学，湖北，武汉
作者邮箱：2014301610173@whu.edu.cn
'''

from tkinter import messagebox
from pyecharts import Scatter3D,Scatter,Bar,Pie,HeatMap,WordCloud
from datetime import *
from dbopr import *
import numpy as np
import time
import threading
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
import jieba
import re
import webbrowser

# 正则过滤
def regex_change(line):
    #前缀的正则
    username_regex = re.compile(r"^\d+::")
    #URL，为了防止对中文的过滤，所以使用[a-zA-Z0-9]而不是\w
    url_regex = re.compile(r"""
        (https?://)?
        ([a-zA-Z0-9]+)
        (\.[a-zA-Z0-9]+)
        (\.[a-zA-Z0-9]+)*
        (/[a-zA-Z0-9]+)*
    """, re.VERBOSE|re.IGNORECASE)
    #剔除日期#utf-8编码
    data_regex = re.compile(u"""        
        年 |
        月 |
        日 |
        (周一) |
        (周二) | 
        (周三) | 
        (周四) | 
        (周五) | 
        (周六)
    """, re.VERBOSE)
    #剔除表情[em]e1232[/em]faf[em]e7552[/em]
    face_regex = re.compile(r"(\[em\]e\d+\[\/em\])")
    #剔除@用户@{uin:df,who:fsdf,nic:sdf}
    user_regex = re.compile(r"(\@\{[\s\S]*?\})")
    #剔除所有数字
    decimal_regex = re.compile(r"[^a-zA-Z]\d+")
    # eng_regex = re.compile(r"[a-zA-Z]")
    #剔除空格
    space_regex = re.compile(r"\s+")

    # line = username_regex.sub(r"", line)
    # line = data_regex.sub(r"", line)
    # line = decimal_regex.sub(r"", line)
    # line = eng_regex.sub(r"",line)

    line = face_regex.sub(r"",line)
    line = user_regex.sub(r"",line)
    line = url_regex.sub(r"", line)
    line = space_regex.sub(r"", line)
    return line

# 按行读取文件，返回文件的行字符串列表
def read_file(file_name):
    fp = open(file_name, "r", encoding="utf-8")
    content_lines = fp.readlines()
    fp.close()
    #去除行末的换行符，否则会在停用词匹配的过程中产生干扰
    for i in range(len(content_lines)):
        content_lines[i] = content_lines[i].rstrip("\n")
    return content_lines

# 剔除停用词
def delete_stopwords(count):
	stopword_file = "stopwords.dat"
	stopwords = read_file(stopword_file)
	res = []
	for i in range(len(count)):
		if(count[i][0] not in stopwords):
			res.append(count[i])
	return res

# 统计评论数、点赞数、日期的最大最小值
def max_min(data):
	# cmtnum,likenum,createtime,comment
	cmtnum = np.array([i[0] for i in data])
	likenum = np.array([i[1] for i in data])
	createtime = np.array([i[2] for i in data])

	cmtnum_min = cmtnum.min()
	cmtnum_max = cmtnum.max()
	likenum_min = likenum.min()
	likenum_max = likenum.max()
	createtime_min = createtime.min()
	createtime_max = createtime.max()
	return cmtnum_min,cmtnum_max,likenum_min,likenum_max,createtime_min,createtime_max

# 二维数组按列排序
def rankcol(data,colnum,order):
	'''ar = np.array(data);
	print(ar.size)
	ar.sort(axis=1)'''
	ar = np.array(data)
	print(ar.dtype)
	br = ar[:,colnum].astype(np.int32)#很关键，定义dtype

	#print(ar[np.argsort(-ar,axis=0)])
	#print(ar[np.lexsort(ar.T)])
	if order == 'des':#降序
		return np.argsort(-br)
	else:#升序
		return np.argsort(br)

# 按点赞或评论数倒序排列
def topfunc(data,num,pos):
	a = rankcol(data,pos,'des')
	resulta = np.array(data)[a]
	return resulta[:num,:]

# 展示label
def label_formatter(params):
	return params[3]
		
# 统计每年的说说数量
def statistic(data):
	count = {}
	for item in data:
		d = datetime.fromtimestamp(item[2])
		count[d.year] = count.get(d.year,0)+1
	print(count)
	return count

# 可视化类
class PaintChart(object):
	# 初始化
	def __init__(self):
		super(PaintChart, self).__init__()

	# 绘图入口
	def Draw(self,sp_ins,curdir,dbname,tablename,chartId):
		sp_ins.analysis_lb.configure(text='正在生成...')
		sp_ins.analysis_pb['value'] = 0

		self.data = getData2Draw(curdir+'/db/'+dbname,tablename)
		self.cmtnum_min,self.cmtnum_max,self.likenum_min,self.likenum_max,self.createtime_min,self.createtime_max = max_min(self.data)
		self.ins = sp_ins
		self.path = curdir+'/chart/'+dbname.split('.')[0]+'/'
		folder = os.path.exists(self.path)
		if not folder: # 判断是否存在文件夹如果不存在则创建为文件夹
			os.makedirs(self.path)

		if(chartId == 0):
			th1 = threading.Thread(target=self.scatter3d, args=())
			th1.start()
		elif(chartId == 1):
			th1 = threading.Thread(target=self.scatter, args=())
			th1.start()
		elif(chartId == 2):
			th1 = threading.Thread(target=self.scatterXY, args=())
			th1.start()
		elif(chartId == 3):
			th1 = threading.Thread(target=self.bar, args=())
			th1.start()
		elif(chartId == 4):
			th1 = threading.Thread(target=self.pie, args=())
			th1.start()
		elif(chartId == 5):
			# year要调整
			year = self.ins.year_entry.get()
			if(year == ''):
				year = datetime.now().year
			elif(year.isdigit()):
				pass
			th1 = threading.Thread(target=self.heatmap, args=(int(year),))
			th1.start()
		elif(chartId == 6):
			th1 = threading.Thread(target=self.wordcloud, args=())
			th1.start()

	# 词云
	def wordcloud(self):
		cmtlist = [i[3] for i in self.data]
		for i in range(len(cmtlist)):
			cmtlist[i] = regex_change(cmtlist[i])# 正则过滤
		txt = " ".join(cmtlist)
		ls = jieba.lcut(txt)
		count = {}
		for word in ls:
			count[word] = count.get(word,0)+1
		items = list(count.items())#元组列表
		items.sort(key=lambda x:x[1],reverse=True)
		items = delete_stopwords(items)
		for i in range(10):
			word,count = items[i]
			print("{0:<10}{1:>5}".format(word,count))
		wordcloud = WordCloud(width=800, height=600)
		wordcloud.add("Top20个人说说词云", [items[i][0] for i in range(20)], [items[i][1] for i in range(20)], word_size_range=[30, 100])
		wordcloud.render(self.path+'wordcloud_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'wordcloud_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

	# 三维散点
	def scatter3d(self):
		for item in self.data:
			d = datetime.fromtimestamp(item[2])
			item[2] = d.year+d.month/12
		range_color = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
		y_min = datetime.fromtimestamp(self.createtime_min).year
		y_max = datetime.fromtimestamp(self.createtime_max).year
		scatter3D = Scatter3D('本人说说点赞数与评论数的时间序列',width=1000,height=800)
		scatter3D.add("",self.data, is_visualmap=True, visual_range_color=range_color,visual_dimension=1,visual_range=[0,70],visual_range_size=[5,20],xaxis3d_name='评论数',yaxis3d_name='点赞数',zaxis3d_min=y_min,zaxis3d_max=y_max,zaxis3d_name='年份')
		scatter3D.render(self.path+'scatter3d_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'scatter3d_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

	# 二维散点
	def scatter(self):
		cmtnum = []
		likenum = []
		timeS = []
		for item in self.data:
			cmtnum.append(item[0])
			likenum.append(item[1])
			d = datetime.fromtimestamp(item[2])
			timeS.append(d.year+d.month/12)
		y_min = datetime.fromtimestamp(self.createtime_min).year
		y_max = datetime.fromtimestamp(self.createtime_max).year
		scatter = Scatter('本人说说点赞数与评论数的时间序列（二维）')
		scatter.add('评论数',timeS,cmtnum,extra_data=cmtnum,xaxis_max=y_max,xaxis_min=y_min,is_datazoom_extra_show=True,datazoom_extra_type='inside',legend_pos='right',xaxis_name='年份',is_visualmap=True,
	    visual_dimension=2,
	    visual_orient="horizontal",
	    visual_type="size",
	    visual_range=[0, 205],
	    visual_range_size=[5,20],
	    visual_text_color="#000")
		scatter.add('点赞数',timeS,likenum,extra_data=likenum,xaxis_max=y_max,xaxis_min=y_min,is_datazoom_extra_show=True,datazoom_extra_type='inside',legend_pos='right',xaxis_name='年份',is_visualmap=True,
	    visual_dimension=2,
	    visual_orient="horizontal",
	    visual_type="size",
	    visual_range=[0,205],
	    visual_range_size=[5,20],
	    visual_text_color="#000")
		scatter.render(self.path+'scatter2d_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'scatter2d_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

	# 线性回归
	def scatterXY(self):
		cmtnum = []
		likenum = []
		shuoshuo = []
		for item in self.data:
			cmtnum.append(item[0])
			likenum.append(item[1])
			shuoshuo.append(item[3])

		regr = linear_model.LinearRegression()
		# Train the model using the training sets
		regr.fit(np.array(likenum)[:-5].reshape(-1,1), np.array(cmtnum)[:-5])
		pred = regr.predict(np.array(likenum)[-5:].reshape(-1,1))
		# The coefficients
		print('Coefficients: \n', regr.coef_)
		print('Intercept:\n',regr.intercept_)
		# Explained variance score: 1 is perfect prediction
		r2 = r2_score(np.array(cmtnum)[-5:],pred)
		print('Variance score: %.2f' % r2)

		scatter = Scatter('本人说说点赞数与评论数关系','评论数 = '+str(regr.coef_[0])+' * 点赞数 + '+str(regr.intercept_)+'    r2 = '+str(r2))
		scatter.add('说说',likenum,cmtnum,extra_data=shuoshuo,symbol_size=5,is_label_show=False,is_label_emphasis=True,label_formatter='{c}',label_emphasis_textcolor='#000',is_datazoom_show=False,is_datazoom_extra_show=False,legend_pos='right',xaxis_name='点赞数',yaxis_name='评论数')
		scatter.render(self.path+'regression_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'regression_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

	# 柱状图
	def bar(self):
		count = statistic(self.data)
		attr = []
		value = []
		for key in count:
			attr.append(key)
			value.append(count[key])
		attr.reverse()
		value.reverse()
		bar = Bar('本人历年说说发表量统计')
		bar.add('说说数',attr,value,xaxis_name='年份')
		bar.render(self.path+'bar_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'bar_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

	# 饼图
	def pie(self):
		toplike = topfunc(self.data,10,1).tolist();
		topctm = topfunc(self.data,10,0).tolist();
		attrlike = [toplike[i][3] for i in range(10)]
		vlike = [toplike[i][1] for i in range(10)]
		attrcmt = [topctm[i][3] for i in range(10)]
		vcmt = [topctm[i][0] for i in range(10)]
		pie = Pie('点赞评论TOP10榜',title_pos='center',subtitle='top:点赞Top10; bottom:评论Top10',width=1200,height=800)
		pie.add(
			"点赞Top10",
			attrlike,
			vlike,
			center=[20,30],
			is_random=True,
			radius=[10,20],
			rosetype="area",
			is_legend_show=True,
			is_label_show=False,
			tooltip_trigger='none',
			label_text_color='#000',
			legend_orient="vertical",
			legend_pos="40%",
			legend_top='center'
			)
		pie.add(
			"评论Top10",
			attrcmt,
			vcmt,
			center=[20,70],
			is_random=True,
			radius=[10,20],
			rosetype="area",
			is_legend_show=True,
			is_label_show=False,
			tooltip_trigger='none',
			label_text_color='#000',
			legend_orient="vertical",
			legend_pos="40%",
			legend_top='center'
			)
		pie.render(self.path+'pie_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'pie_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

	# 热力图
	def heatmap(self,year):
		das = {}
		for item in self.data:
			d = datetime.fromtimestamp(item[2])
			if(d.year == year):
				das[date(d.year,d.month,d.day)] = das.get(date(d.year,d.month,d.day),0)+item[1]
		result = [[str(key),das[key]] for key in das]
		y_min = min([das[key] for key in das])
		y_max = max([das[key] for key in das])
		heatmap = HeatMap('说说点赞之日历热力图',title_pos='center',width=1100)
		heatmap.add(
			"",
			result,
			is_calendar_heatmap=True,
			visual_text_color='#000',
			visual_range_text=["",""],
			visual_range=[y_min,y_max],
			calendar_cell_size=["auto",30],
			is_visualmap=True,
			calendar_date_range=str(year),
			visual_orient="horizontal",
			visual_pos='center',
			visual_top='80%',
			is_piecewise=True
			)
		heatmap.render(self.path+'heatmap'+str(year)+'_'+str(int(time.time()))+'.html')
		webbrowser.open_new_tab(self.path+'heatmap'+str(year)+'_'+str(int(time.time()))+'.html')
		self.ins.analysis_pb['value'] = 100
		self.ins.analysis_lb.configure(text='完毕')

			