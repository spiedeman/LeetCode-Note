#  from crawler import Crawler
from a import Crawler
from html2md import HTML2MARKDOWN
import os
import sys
import time

LOCAL_PATH=os.path.split(os.path.abspath(sys.argv[0]))[0]
t0 = time.time()
# 创建实例
leetcode = Crawler()
leetcode.login()

# 获取本地和官网题目集合
local_problems = leetcode.local_problems_list()
#  cloud_problems = leetcode.cloud_problems_list()
#  data = set(cloud_problems.keys())
print(local_problems)
#  print(cloud_problems)

# 通过题目编号查询题目信息
# 若不在本地，则联网查询并更新本地数据库
i = 1
#  problem = leetcode.query(i)
#  print(problem.keys())

# 把问题描述转成 markdown 格式
# 并通过模版文件生成完整解答
#  description = HTML2MARKDOWN(problem)
#  description.rigister()
#  description.convert()
#  print(description.content)

# 修改几个文件
# _sidebar.md
# link_path.md
# README.md
# answer_list.md

def add_answer(i):
    problem = leetcode.query(i)
    filename = '{}.{}.md'.format(problem['frontend_id'], problem['title_zh'])
    filepath = LOCAL_PATH+'/docs/Solutions'

    keys = ['{}link'.format(i), '{}path'.format(i)]
    values = [problem['url'], filename]
    link_path = dict(zip(keys, values))
    
    answer = HTML2MARKDOWN(problem, output=filename, path=filepath)

    answer.rigister()
    answer.convert()
    answer.write()

    with open(filepath+'/answer_list.md', 'r') as f:
        #  content = ''.join(f.readlines())
        content = f.readlines()
        content = ''.join(content)
        add_content = '- [x] [{} {}][{}path]'.format(i, problem['title_zh'], i)
        content = content.strip()+'\n'
        content += add_content
        print(content)

        #  f.write(content)

    with open(filepath+'/../link_path.md', 'r') as f:
        content = f.readlines()
        content = ''.join(content)
        content = content.strip()+'\n'
        add_content = '[{}link]: {}\n'.format(i, problem['url'])
        add_content += '[{}path]: Solutions/{}.{}.md\n'.format(i, i, problem['title_zh'])
        content += add_content
        print(content)

    with open(filepath + '/../_sidebar.md', 'r') as f:
        content = f.readlines()
        content = ''.join(content)
        content = content.strip()+'\n'
        add_content = '  * [{}](Solutions/{}.{}.md)'.format(i, i, problem['title_zh'])
        content += add_content
        print(content)

add_answer(i)
