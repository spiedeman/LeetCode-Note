import os
import sys
from crawler import Crawler
from html2md import HTML2MARKDOWN

LOCAL_PATH=os.path.split(os.path.abspath(sys.argv[0]))[0]

def add_answer(frontend_id=1):
    """
    添加编号为 frontend_id 的问题的解答，并对相关文件做相应的修改
    
    - README， /docs/Solutions/answer_list.md
    - 定义， /docs/link_path.md
    - 目录， /docs/_sidebar.md
    """
    leetcode = Crawler()
    problem = leetcode.query(frontend_id)

    filename = '{:04d}.{}.md'.format(problem['frontend_id'], problem['title_zh'])
    filepath = LOCAL_PATH+'/docs/Solutions'

    plink = '{:04d}link'.format(frontend_id)
    ppath = '{:04d}path'.format(frontend_id)
    
    answer = HTML2MARKDOWN(problem, output=filename, solution_path=filepath)

    # 添加解答文件
    answer.rigister()
    answer.convert()
    answer.write()

    # 修改 /docs/Solutions/answer_list.md
    with open(filepath+'/answer_list.md', 'r') as f:
        content = [line.strip('\n') for line in f.readlines()]
        content.append('- [x] [{:04d} {}][{}]'.format(frontend_id, problem['title_zh'].replace('-', ' '), ppath))
        j = 0
        while not content[j] or content[j][0] != '-':
            j += 1
        content = '\n'.join(content[:j] + sorted(set(content[j:])))
    with open(filepath+'/answer_list.md', 'w') as f:
        f.write(content)

    # 修改 /docs/link_path.md
    with open(filepath+'/../link_path.md', 'r') as f:
        content = [line.strip('\n') for line in f.readlines()]
        content.append('[{}]: {}'.format(plink, problem['url']))
        content.append('[{}]: Solutions/{:04d}.{}.md'.format(ppath, frontend_id, problem['title_zh']))
        content = '\n'.join(sorted(set(content)))
    with open(filepath+'/../link_path.md', 'w') as f:
        f.write(content)

    # 修改 /docs/_sidebar.md
    with open(filepath+'/../_sidebar.md', 'r') as f:
        content = [line.strip('\n') for line in f.readlines()]
        content.append('  * [{:04d}](Solutions/{:04d}.{}.md)'.format(frontend_id, frontend_id, problem['title_zh']))
        j = 0
        while content[j][0] == '*':
            j += 1
        content = '\n'.join(content[:j] + sorted(set(content[j:])))
    with open(filepath+'/../_sidebar.md', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    print(sys.argv[1])
