import os
import sys
import json
import requests
import sqlite3

path=os.path.split(os.path.abspath(sys.argv[0]))[0]

class Crawler(object):

    """
    LeetCode 爬虫
    """

    def __init__(self):
        self.auth = {'username': 'spiedeman', 'password': 'xinmima3#'}
        conn = None
        self.stats = None
        self.database = path+'/leetcode.db'
        self.database_name = ['leetcode_problems_stats',
                       'leetcode_problems_description']
        self.database_checked = False
        self.baseurl = 'https://leetcode-cn.com/'
        self.csrftoken = ''
        self.useragent = {
                'Safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
                'Chrome': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36'
                }
        self.session = requests.Session()
        self.is_login = False


    def login(self):
        loginurl = self.baseurl+'accounts/login/'
        headers = {'User-Agent': self.useragent['Safari'], 'Connection': 'keep-alive', 'Referer': loginurl, 'origin': 'https://leetcode-cn.com'}
        token = self.session.get(loginurl).cookies['csrftoken']
        post_data = {
                'csrfmiddlewaretoken': token,
                'login': self.auth['username'],
                'password': self.auth['password']
                }
        page = self.session.post(loginurl, data=post_data, headers=headers, timeout=10)
        if not self.session.cookies.get('LEETCODE_SESSION'):
            self.is_login = False
        else:
            self.is_login = True

    def query(self, frontend_id=1):
        """
        仅支持通过题目编号(frontend_id)来查询题目信息
        若该题目不在本地数据库，则联网获取信息并更新本地数据库
        """
        problem = ['frontend_id', 'url', 'slug', 'accept_ratio', 'status',
                'difficulty', 'title_zh', 'content_zh']
        self.connect_db()
        cursor = self.conn.cursor()
        # 先在本地查找题目基本信息
        cursor.execute('select * from {} where frontend_id={}'.format(self.database_name[0], frontend_id))
        local_result = cursor.fetchone()
        if local_result:
            content = list(local_result)[1:]
        else:
            # 本地不存在，联网获取题目信息
            cloud_problems = self.cloud_problems_list()
            # 更新本地数据库
            cursor.execute('insert into {} (frontend_id, url, slug, ac_ratio, status, difficulty) values(?,?,?,?,?,?)'.format(self.database_name[0]), cloud_problems[frontend_id])
            content = list(cloud_problems[frontend_id])

        # 先在本地查找中文题目和描述
        cursor.execute('select title_zh, content_zh from {} where frontend_id={}'.format(self.database_name[1], frontend_id))
        local_result = cursor.fetchone()
        if local_result:
            content.extend(list(local_result))
        else:
            # 本地不存在，联网获取中文标题和题目描述
            url = content[1]
            slug = content[2]
            response = self.get_problem_description(url, slug)
            result = (frontend_id, response['translatedTitle'], response['translatedContent'], response['questionTitle'], response['content'])
            # 更新本地数据库
            cursor.execute('insert into {} (frontend_id, title_zh, content_zh, title, content) values(?,?,?,?,?)'.format(self.database_name[1]), result)
            content.extend([result[1], result[2]])
        # 以字典方式返回题目信息
        problem = dict(zip(problem, content))
        cursor.close()
        self.close_db()
        
        return problem

    def local_problems_list(self):
        """
        从数据库获取当前已有的题目集合，以 frontend_id 标识
        """
        self.connect_db()
        cursor = self.conn.cursor()
        cursor.execute('select frontend_id from {}'.format(self.database_name[0]))         
        problems_exists = set(record[0] for record in cursor.fetchall())
        cursor.close()
        self.close_db()
        return problems_exists

    def cloud_problems_list(self):
        url = self.baseurl + 'api/problems/algorithms/'
        soup = json.loads(self.session.get(url).text)
        self.stats = soup
        
        data = self.stats.pop('stat_status_pairs')
        problems_latest = dict()
        for problem in data:
            frontend_id = problem['stat']['frontend_question_id']
            slug = problem['stat']['question__title_slug']
            problemURL = self.baseurl + 'problems' + slug
            accept_ratio = problem['stat']['total_acs']/problem['stat']['total_submitted'] 
            status = problem['status']
            difficulty = problem['difficulty']['level']
            problems_latest[frontend_id] = (frontend_id, problemURL, slug,
                accept_ratio, status, difficulty)

        return problems_latest

    def local_problems_description(self):
        """
        从数据库获取已有的题目描述的集合，以 frontend_id 标识
        """
        self.connect_db()
        cursor = self.conn.cursor()
        cursor.execute('select frontend_id from {}'.format(slef.database_name[1]))
        description_exists = set(record[0] for record in cursor.fetchall())
        cursor.close()
        self.close_db()
        return description_exists

    def get_problem_description(self, problemURL, titleslug):
        session = requests.Session()
        url = 'https://leetcode-cn.com/graphql'
        data = {"operationName":"getQuestionDetail",
            "variables":{"titleSlug":titleslug},
            'query': '''query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                   questionTitle
                   translatedTitle
                   content
                   translatedContent
                   similarQuestions
                   categoryTitle
            }
        }'''
        }
        headers = {'User-Agent': self.useragent['Safari'],'Connection':'keep-alive',
                'Content-Type':'application/json', 'Referer':problemURL}

        page = session.post(url, data=json.dumps(data).encode(), headers=headers, timeout=10).json()
        #  print(page['data']['question'])
        return page['data']['question']

    def update_db(self):
        local_problems = self.local_problems_list()
        cloud_problems = self.cloud_problems_list()
        update_problems = [cloud_problems[i] for i in set(cloud_problems.keys()).difference(local_problems)]
        # 官网有新题目加入时，更新数据库
        if not update_problems:
            slef.connect_db()
            cursor = self.conn.cursor()
            cursor.executemany('insert into {} (frontend_id, url, slug, ac_ratio, status, difficulty) values(?,?,?,?,?,?)'.format(self.database_name[0]), update_problems)
        
        # 有新题目时，更新题目描述，包括中文和英文
        local_descriptions = self.local_problems_description()
        update_descriptions = set(cloud_problems_list.keys()).difference(local_descriptions)
        if not update_descriptions:
            if self.conn is None:
                self.connect_db()
            update_data = []
            for i in update_descriptions:
                url, slug = cloud_problems[i][1], cloud_problems[i][2]
                response = self.get_problem_description(url, slug)
                update_data.append((i, response['translatedTitle'],
                    response['translatedContent'], response['questionTitle'],
                    response['content']))
            # 一次性将所有更新数据写入数据库
            cursor.executemany('insert into {} (frontend_id, title_zh, content_zh, title, content)'.format(self.database_name[1]), update_data)

        cursor.close()
        self.close_db()

    def check_db(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        # 查找已有的所有表
        cursor.execute("select * from sqlite_master where type='table'")
        table_exists = set([table[1] for table in cursor.fetchall()])
        table_names = ['leetcode_problems_stats',
                       'leetcode_problems_description']
        # 维护两张表，若不存在则建立
        t_name = self.database_name[0]
        if t_name not in table_exists:
            cursor.execute('''CREATE TABLE {}
            (id integer primary key, frontend_id integer, url text, slug text, 
            ac_ratio real, status text, difficulty integer)'''.format(t_name))

        t_name = self.database_name[1]
        if t_name not in table_exists:
            cursor.execute('''CREATE TABLE {}
            (id integer primary key, frontend_id integer, title_zh text, 
            content_zh text, title text, content text)'''.format(t_name))
        cursor.close()
        conn.commit()
        conn.close()
        self.database_checked = True

    def connect_db(self):
        if not self.database_checked:
            self.check_db()
        self.conn = sqlite3.connect(self.database)

    def close_db(self):
        self.conn.commit()
        self.conn.close()
        self.conn = None
