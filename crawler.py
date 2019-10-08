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
        if token:
            print('成功获取token')
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
        #  print(local_tables)
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
          - value: 一个tuple，与table(problem_list)中字段排序一致
        """
        if not self.is_login:
            # 若未登陆，则无法获得正确的题目状态
            print('not login yet')
            self.login()
        else:
            print('login already')
        url = '{}/api/problems/algorithms/'.format(self.baseurl)
        response = json.loads(self.session.get(url).text)
        print(response['stat_status_pairs'])
        cloud_problems = dict()
        print('got problems')
        for problem in response.pop('stat_status_pairs'):
            # 顺序很重要
            # frontend_id, problemURL, slug, accept_ratio, status, level
            info = [problem['stat']['frontend_question_id']]
            info.append('{}/problems/{}'.format(self.baseurl, problem['stat']['question__title_slug']))
            info.append(problem['stat']['question__title_slug'])
            info.append(problem['stat']['total_acs']/problem['stat']['total_submitted'])
            info.append(problem['status'])
            info.append(problem['difficulty']['level'])
            cloud_problems[info[0]] = tuple(info)
        return cloud_problems

    @connect_db
    def local_problems_description(self):
        """
        set: 包含table(problem_detail)中所有题目的frontend_id
        """
        cursor = self.conn.cursor()
        cursor.execute('select frontend_id from {}'.format(self.db_tables[1]))
        local_descriptions = set(record[0] for record in cursor.fetchall())
        cursor.close()
        return local_descriptions

    def cloud_problems_description(self, titleslug):
        """
        tuple: 与table(problem_detail)中字段的顺序一致
        """
        session = requests.Session()
        url = 'https://leetcode-cn.com/graphql'
        post_data = {"operationName":"questionData",
            "variables":{"titleSlug":titleslug},
            'query': '''query questionData($titleSlug: String!) {
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
        problemURL = '{}/problems/{}'.format(self.baseurl, titleslug)
        headers = {'User-Agent': self.useragent['Safari'],'Connection':'keep-alive', 'Content-Type':'application/json', 'Referer':problemURL}

        response = session.post(url, data=json.dumps(post_data).encode(), headers=headers, timeout=10).json()['data']['question']
        response = (response['questionFrontendId'], response['translatedTitle'].replace(' ', '-'), response['translatedContent'], response['questionTitle'], response['content'])
        return response

    def cloud_problem_submission(self, titleslug):
        """
        必须先登陆，再根据题目 slug 获取提交信息
        """
        if not self.is_login:
            self.login()
        url = 'https://leetcode-cn.com/graphql'
        post_data = {"operationName":"Submissions",
        "variables":{"offset":0,"limit":20,"lastKey":'',"questionSlug":titleslug},
            "query":'''query Submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!) {
                submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug) {
                    lastKey
                    hasNext
                    submissions {
                        id
                        statusDisplay
                        lang
                        runtime
                        timestamp
                        url
                        isPending
                        memory
                        __typename
                    }
                    __typename
                }
            }'''
        }

        problemURL = '{}/problems/{}'.format(self.baseurl, titleslug)
        headers = {'User-Agent': self.useragent['Safari'],'Connection':'keep-alive', 'Content-Type':'application/json', 'Referer':problemURL}

        response = self.session.post(url, data=json.dumps(post_data).encode(), headers=headers, timeout=10).json()
        response = response['data']['submissionList']['submissions']
        return response

    @connect_db
    def query(self, frontend_id=1):
        """
        仅支持通过题目编号(frontend_id)来查询题目信息
        若该题目不在本地数据库，则联网获取信息并更新本地数据库
        Return
        ======
        dict: keys = [frontend_id, url, slug, accept_ratio, status, level, title_zh, content_zh] 
        """
        #  print(hasattr(self, 'conn'), '\tself.conn')
        cursor = self.conn.cursor()
        # 查询 table1——problem_list
        cursor.execute('select * from {} where frontend_id={}'.format(self.db_tables[0], frontend_id))
        local_result = cursor.fetchone()
        if local_result:
            print('题目基本信息来自于本地数据库')
            response = list(local_result[1:])
        else:
            # 总的题目列表更新至本地数据库
            print('从官网获取基本信息中...')
            cloud_problems = self.cloud_problems_list()
            cursor.executemany('insert into {} (frontend_id, url, slug, ac_ratio, status, level) values(?,?,?,?,?,?)'.format(self.db_tables[0]), cloud_problems.values())
            response = list(cloud_problems[frontend_id])
            if response:
                print('题目基本信息获取成功！')

        # 查询 table2——problem_detail
        cursor.execute('select title_zh, content_zh from {} where frontend_id={}'.format(self.db_tables[1], frontend_id))
        local_result = cursor.fetchone()
        if local_result:
            print('题目详细信息来自于本地数据库')
            response.extend(list(local_result))
        else:
            # 仅更新编号为frontend_id的题目描述等详细内容至本地数据库
            print('从官网获取题目描述等详细信息中...')
            slug = response[2]
            rm_response = self.cloud_problems_description(slug)
            #  print(rm_response)
            cursor.execute('insert into {} (frontend_id, title_zh, content_zh, title, content) values(?,?,?,?,?)'.format(self.db_tables[1]), rm_response)
            response.extend(list(rm_response[1:3]))
            print('题目描述等详细信息获取成功！')
        
        keys = ['frontend_id', 'url', 'slug', 'accept_ratio', 'status', 'level', 'title_zh', 'content_zh']
        result = dict(zip(keys, response))
        # 若已提交，则获取提交信息
        if result['status'] == 'ac':
            try:
                result['submission'] = self.cloud_problem_submission(result['slug'])
            except:
                result['submission'] = 'fetch submission info failed!'

        cursor.close()
        return result

    @connect_db
    def update_db(self):
        cursor = self.conn.cursor()

        # 官网有新题目加入时，更新数据库
        local_problems = self.local_problems_list()
        cloud_problems = self.cloud_problems_list()
        update_problems = [cloud_problems[i] for i in set(cloud_problems.keys()).difference(local_problems)]
        if update_problems:
            print('将新增题目基本信息更新至数据库中...')
            cursor.executemany('insert into {} (frontend_id, url, slug, ac_ratio, status, level) values(?,?,?,?,?,?)'.format(self.db_tables[0]), update_problems)
            print('新增题目基本信息更新完毕')

        # 有新题目时，更新题目描述，包括中文和英文
        local_descriptions = self.local_problems_description()
        update_descriptions = set(cloud_problems.keys()).difference(local_descriptions)
        if update_descriptions:
            print('将新增题目详细信息更新之数据库中...')
            update_data = []
            for i in update_descriptions:
                slug = cloud_problems[i][2]
                response = self.cloud_problems_description(slug)
                update_data.append(response)
            # 一次性将所有更新数据写入数据库
            cursor.executemany('insert into {} (frontend_id, title_zh, content_zh, title, content) values(?,?,?,?,?)'.format(self.db_tables[1]), update_data)
            print('新增题目详细信息更新完毕')

        cursor.close()


if __name__ == "__main__":
    leetcode = Crawler()
    if len(sys.argv) > 1:
        problem_id = sys.argv[1]
    else:
        problem_id = 306
    #  print(leetcode.is_login)
    print(leetcode.login())
    #  print(leetcode.is_login)

    #  print(leetcode.cloud_problems_list())
    #  print(leetcode.db_checked, '\tself.db_checked')
    #  print(hasattr(leetcode, 'conn'), '\tself.conn')
    #  question = leetcode.query(problem_id)
    #  print(question)
    #  print(leetcode.local_problems_description())
    #  print(len(leetcode.local_problems_list()))
    #  print(leetcode.db_checked, '\tself.db_checked')
    #  print(hasattr(leetcode, 'conn'), '\tself.conn')
    #  leetcode.update_db()
