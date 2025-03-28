# 数据爬取文件

import scrapy
import pymysql
import pymssql
from ..items import PanjuxinxiItem
import time
import re
import random
import platform
import json
import os
from urllib.parse import urlparse
import requests
import emoji

# 番剧信息
class PanjuxinxiSpider(scrapy.Spider):
    name = 'panjuxinxiSpider'
    spiderUrl = 'https://api.bilibili.com/pgc/season/index/result?season_version=-1&spoken_language_type=-1&area=-1&is_finish=-1&copyright=-1&season_status=-1&season_month=-1&year=-1&style_id=-1&order=3&st=1&sort=0&page={}&season_type=1&pagesize=20&type=1'
    start_urls = spiderUrl.split(";")
    protocol = ''
    hostname = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start_requests(self):

        plat = platform.system().lower()
        if plat == 'linux' or plat == 'windows':
            connect = self.db_connect()
            cursor = connect.cursor()
            if self.table_exists(cursor, 'rz34k_panjuxinxi') == 1:
                cursor.close()
                connect.close()
                self.temp_data()
                return

        pageNum = 1 + 1
        for url in self.start_urls:
            if '{}' in url:
                for page in range(1, pageNum):
                    next_link = url.format(page)
                    yield scrapy.Request(
                        url=next_link,
                        callback=self.parse
                    )
            else:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse
                )

    # 列表解析
    def parse(self, response):
        
        _url = urlparse(self.spiderUrl)
        self.protocol = _url.scheme
        self.hostname = _url.netloc
        plat = platform.system().lower()
        if plat == 'windows_bak':
            pass
        elif plat == 'linux' or plat == 'windows':
            connect = self.db_connect()
            cursor = connect.cursor()
            if self.table_exists(cursor, 'rz34k_panjuxinxi') == 1:
                cursor.close()
                connect.close()
                self.temp_data()
                return

        data = json.loads(response.body)
        list = data["data"]["list"]
        
        for item in list:

            fields = PanjuxinxiItem()

            fields["laiyuan"] = item["link"]
            fields["biaoti"] = item["title"]
            fields["zibiaoti"] = item["subTitle"]
            fields["pingfen"] = item["score"]
            fields["fengmian"] = item["cover"]
            fields["xuanji"] = item["index_show"]
            fields["epid"] = item["first_ep"]["ep_id"]


            detailUrlRule = 'https://api.bilibili.com/pgc/view/web/season?ep_id={0}'.format(fields["epid"])

            if detailUrlRule.startswith('http') or self.hostname in detailUrlRule:
                pass
            else:
                detailUrlRule = self.protocol + '://' + self.hostname + detailUrlRule
                fields["laiyuan"] = detailUrlRule

            yield scrapy.Request(url=detailUrlRule, meta={'fields': fields}, callback=self.detail_parse)

    # 详情解析
    def detail_parse(self, response):
        fields = response.meta['fields']

        res = json.loads(response.text)

        fields["pingjia"] = res["result"]["evaluate"]
        fields["bofangliang"] = res["result"]["stat"]["views"]
        fields["danmu"] = res["result"]["stat"]["danmakus"]
        fields["pfrs"] = res["result"]["rating"]["count"]

        return fields

    # 去除多余html标签
    def remove_html(self, html):
        if html == None:
            return ''
        pattern = re.compile(r'<[^>]+>', re.S)
        return pattern.sub('', html).strip()

    # 数据库连接
    def db_connect(self):
        type = self.settings.get('TYPE', 'mysql')
        host = self.settings.get('HOST', 'localhost')
        port = int(self.settings.get('PORT', 3306))
        user = self.settings.get('USER', 'root')
        password = self.settings.get('PASSWORD', '123456')

        try:
            database = self.databaseName
        except:
            database = self.settings.get('DATABASE', '')

        if type == 'mysql':
            connect = pymysql.connect(host=host, port=port, db=database, user=user, passwd=password, charset='utf8')
        else:
            connect = pymssql.connect(host=host, user=user, password=password, database=database)

        return connect

    # 断表是否存在
    def table_exists(self, cursor, table_name):
        cursor.execute("show tables;")
        tables = [cursor.fetchall()]
        table_list = re.findall('(\'.*?\')',str(tables))
        table_list = [re.sub("'",'',each) for each in table_list]

        if table_name in table_list:
            return 1
        else:
            return 0

    # 数据缓存源
    def temp_data(self):

        connect = self.db_connect()
        cursor = connect.cursor()
        sql = '''
            insert into panjuxinxi(
                id
                ,laiyuan
                ,biaoti
                ,zibiaoti
                ,pingfen
                ,fengmian
                ,xuanji
                ,epid
                ,pingjia
                ,bofangliang
                ,danmu
                ,pfrs
            )
            select
                id
                ,laiyuan
                ,biaoti
                ,zibiaoti
                ,pingfen
                ,fengmian
                ,xuanji
                ,epid
                ,pingjia
                ,bofangliang
                ,danmu
                ,pfrs
            from rz34k_panjuxinxi
            where(not exists (select
                id
                ,laiyuan
                ,biaoti
                ,zibiaoti
                ,pingfen
                ,fengmian
                ,xuanji
                ,epid
                ,pingjia
                ,bofangliang
                ,danmu
                ,pfrs
            from panjuxinxi where
                panjuxinxi.id=rz34k_panjuxinxi.id
            ))
            limit {0}
        '''.format(random.randint(20,30))

        cursor.execute(sql)
        connect.commit()

        connect.close()
