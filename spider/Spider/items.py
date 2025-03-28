# 数据容器文件

import scrapy

class SpiderItem(scrapy.Item):
    pass

class PanjuxinxiItem(scrapy.Item):
    # 来源
    laiyuan = scrapy.Field()
    # 标题
    biaoti = scrapy.Field()
    # 子标题
    zibiaoti = scrapy.Field()
    # 评分
    pingfen = scrapy.Field()
    # 封面
    fengmian = scrapy.Field()
    # 选集
    xuanji = scrapy.Field()
    # epid
    epid = scrapy.Field()
    # 评价
    pingjia = scrapy.Field()
    # 播放量
    bofangliang = scrapy.Field()
    # 弹幕量
    danmu = scrapy.Field()
    # 评分人数
    pfrs = scrapy.Field()

