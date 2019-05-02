from crawler import Crawler
from html2md import HTML2MARKDOWN
import time

t0 = time.time()
# 创建实例
leetcode = Crawler()
leetcode.login()

# 获取本地和官网题目集合
local_problems = leetcode.local_problems_list()
cloud_problems = leetcode.cloud_problems_list()
data = set(cloud_problems.keys())
print(local_problems)
#  print(cloud_problems)

# 通过题目编号查询题目信息
# 若不在本地，则联网查询并更新本地数据库
i = 1031
problem = leetcode.query(i)
print(problem.keys())

# 把问题描述转成 markdown 格式
# 并通过模版文件生成完整解答
description = HTML2MARKDOWN(problem)
description.rigister()
description.convert()
print(description.content)
