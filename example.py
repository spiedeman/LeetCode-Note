from crawler import Crawler

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
i = 1030
print(leetcode.query(i))
