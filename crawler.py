import os
import sys
import json
import requests
import sqlite3

class Crawler(object):
    """
    LeetCode 爬虫
    """
    def __init__(self):
        self.auth = {'username': 'spiedeman', 'password': 'xinmima3#'}
        self.baseurl = 'https://leetcode-cn.com'
        self.csrftoken = ''
        self.useragent = {
                'Safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
                'Chrome': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36'
                }
        self.session = requests.Session()
        self.is_login = False

        self.db_dir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        self.db_path = '{}/leetcode.db'.format(self.db_dir)
        self.db_tables = ['problem_list', 'problem_detail']
        self.db_column = ['(id integer primary key, frontend_id integer, url text, slug text, ac_ratio real, status text, level integer)', 
                          '(id integer primary key, frontend_id integer, title_zh text, content_zh text, title text, content text)']
        self.db_checked = False

    def login(self):
        login_url = '{}/accounts/login/'.format(self.baseurl)
        headers = {'User-Agent': self.useragent['Safari'],
                   'Connection': 'keep-alive',
                   'Referer': login_url,
                   'origin': self.baseurl}
        token = self.session.get(login_url).cookies['csrftoken']
        post_data = {'csrfmiddlewaretoken': token,
                     'login': self.auth['username'],
                     'password': self.auth['password']}
        page = self.session.post(login_url, data=post_data,
                headers=headers, timeout=10)
        if not self.session.cookies.get('LEETCODE_SESSION'):
            self.is_login = False
        else:
            self.is_login = True
    
    def check_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("select * from sqlite_master where type='table'")
        local_tables = set([table[1] for table in cursor.fetchall()])
        print(local_tables)
        for table, column in zip(self.db_tables, self.db_column):
            if table not in local_tables:
                cursor.execute('''CREATE TABLE {} {}'''.format(table, column))
        cursor.close()
        conn.commit()
        conn.close()
        self.db_checked = True

    def connect_db(func):
        def wrapper(self, *args, **kwargs):
            if not self.db_checked:
                self.check_db()
            self.conn = sqlite3.connect(self.db_path)
            result = func(self, *args, **kwargs)

            self.conn.commit()
            self.conn.close()
            del self.conn
            return result
        return wrapper

    @connect_db
    def local_problems_list(self):
        """
        Return
        ======
        set: 包含table(problem_list)中所有题目的frontend_id
        """
        cursor = self.conn.cursor()
        cursor.execute('select frontend_id from {}'.format(self.db_tables[0]))
        local_problems = set(record[0] for record in cursor.fetchall())
        cursor.close()
        return local_problems

    def cloud_problems_list(self):
        """
        Return
        ======
        dict: 包含所有题目
          - key: frontend_id
          - value: 以table(problem_list)中字段排序的一个tuple
        """
        if not self.is_login:
            print('not login yet')
            self.login()
        else:
            print('login already')
        url = '{}/api/problems/algorithms/'.format(self.baseurl)
        response = json.loads(self.session.get(url).text)
        cloud_problems = dict()
        print('got problems')
        for problem in response.pop('stat_status_pairs'):
            # 顺序很重要
            # frontend_id, problemURL, slug, accept_ratio, status, level
            info = [problem['stat']['frontend_question_id']]
            info.append('{}/problems/{}'.format(self.baseurl, info[-1]))
            info.append(problem['stat']['question__title_slug'])
            info.append(problem['stat']['total_acs']/problem['stat']['total_submitted'])
            info.append(problem['status'])
            info.append(problem['difficulty']['level'])
            cloud_problems[info[0]] = tuple(info)
        return cloud_problems

    @connect_db
    def local_problems_description(self):
        """
        从数据库table(problem_detail)获取所有题目的frontend_id构成的set
        """
        cursor = self.conn.cursor()
        cursor.execute('select frontend_id from {}'.format(self.db_tables[1]))
        local_descriptions = set(record[0] for record in cursor.fetchall())
        cursor.close()
        return local_descriptions

    def get_problem_description(self, problemURL, titleslug):
        """
        按照table(problem_detail)中字段的顺序返回一个tuple
        """
        session = requests.Session()
        url = 'https://leetcode-cn.com/graphql'
        post_data = {"operationName":"getQuestionDetail",
            "variables":{"titleSlug":titleslug},
            'query': '''query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                   questionTitle
                   translatedTitle
                   content
                   translatedContent
                   questionFrontendId
                   similarQuestions
                   categoryTitle
            }
        }'''
        }
        headers = {'User-Agent': self.useragent['Safari'],'Connection':'keep-alive', 'Content-Type':'application/json', 'Referer':problemURL}

        response = session.post(url, data=json.dumps(post_data).encode(), headers=headers, timeout=10).json()['data']['question']
        response = (response['questionFrontendId'], response['translatedTitle'], response['translatedContent'], response['questionTitle'], response['content'])
        return response

    @connect_db
    def query(self, frontend_id=1):
        """
        仅支持通过题目编号(frontend_id)来查询题目信息
        若该题目不在本地数据库，则联网获取信息并更新本地数据库
        """
        #  print(hasattr(self, 'conn'), '\tself.conn')
        cursor = self.conn.cursor()
        # 查询 table1——problem_list
        cursor.execute('select * from {} where frontend_id={}'.format(self.db_tables[0], frontend_id))
        local_result = cursor.fetchone()
        if local_result:
            response = list(local_result[1:])
        else:
            # 总的题目列表更新至本地数据库
            cloud_problems = self.cloud_problems_list()
            cursor.executemany('insert into {} (frontend_id, url, slug, ac_ratio, status, level) values(?,?,?,?,?,?)'.format(self.db_tables[0]), cloud_problems.values())
            response = list(cloud_problems[frontend_id])

        # 查询 table2——problem_detail
        cursor.execute('select title_zh, content_zh from {} where frontend_id={}'.format(self.db_tables[1], frontend_id))
        local_result = cursor.fetchone()
        if local_result:
            response.extend(list(local_result))
        else:
            # 仅更新编号为frontend_id的题目描述等详细内容至本地数据库
            url, slug = response[1:3]
            rm_response = self.get_problem_description(url, slug)
            print(rm_response)
            cursor.execute('insert into {} (frontend_id, title_zh, content_zh, title, content) values(?,?,?,?,?)'.format(self.db_tables[1]), rm_response)
            response.extend(list(rm_response[1:3]))
        
        keys = ['frontend_id', 'url', 'slug', 'accept_ratio', 'status', 'level', 'title_zh', 'content_zh']
        cursor.close()
        return dict(zip(keys, response))

    @connect_db
    def update_db(self):
        cursor = self.conn.cursor()

        # 官网有新题目加入时，更新数据库
        local_problems = self.local_problems_list()
        cloud_problems = self.cloud_problems_list()
        update_problems = [cloud_problems[i] for i in set(cloud_problems.keys()).difference(local_problems)]
        if not update_problems:
            cursor.executemany('insert into {} (frontend_id, url, slug, ac_ratio, status, level) values(?,?,?,?,?,?)'.format(self.db_tables[0]), update_problems)

        # 有新题目时，更新题目描述，包括中文和英文
        local_descriptions = self.local_problems_description()
        update_descriptions = set(cloud_problems_list.keys()).difference(local_descriptions)
        if not update_descriptions:
            update_data = []
            for i in update_descriptions:
                url, slug = cloud_problems[i][1:3]
                response = self.get_problem_description(url, slug)
                update_data.append(response)
            # 一次性将所有更新数据写入数据库
            cursor.executemany('insert into {} (frontend_id, title_zh, content_zh, title, content) values(?,?,?,?,?)'.format(self.db_tables[1]), update_data)

        cursor.close()


#  leetcode = Crawler()
#  print(leetcode.db_checked, '\tself.db_checked')
#  print(hasattr(leetcode, 'conn'), '\tself.conn')
#  #  print(leetcode.query())
#  print(leetcode.local_problems_description())
#  #  print(len(leetcode.local_problems_list()))
#  print(leetcode.db_checked, '\tself.db_checked')
#  print(hasattr(leetcode, 'conn'), '\tself.conn')

