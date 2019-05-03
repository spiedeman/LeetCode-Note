import os
import sys
import re
from functools import partial

LOCAL_PATH=os.path.split(os.path.abspath(sys.argv[0]))[0]

class HTML2MARKDOWN(object):
    def __init__(self, info=dict(), output='output.md', path='.'):
        self.info = info
        self.content = ''
        self.output = output
        self.path = path
        self.rules = []

    def template(self):
        #  page = '''# [{}-{}]({})\n\n[答案列表](Solutions/answer_list.md)\n## 题目描述\n{}\n\n## 题目分析\n\n## Code\n'''
        with open(LOCAL_PATH+'/template.md', 'r') as f:
            page = ''.join(f.readlines())

        return page

    def convert(self):
        """
        根据注册的规则将 html 文本转换为 markdown 格式
        """
        level = {1: '简单', 2: '中等', 3: '困难'}
        is_ac = {None: '未做', 'ac': '已解答'}
        frontend_id = self.info['frontend_id']
        url = self.info['url']
        status = is_ac[self.info['status']]
        accept_ratio = 100 * self.info['accept_ratio']
        difficulty = level[self.info['level']]
        title = self.info['title_zh']
        content = self.info['content_zh']
        
        if not self.rules:
            self.rigister()
        for rule in self.rules:
            pat, repl = rule
            content = re.sub(pat, repl, content)
        
        form = (frontend_id, title, url, status, accept_ratio, difficulty, content)
        
        self.content = self.template().format(*form)

    def write(self):
        """
        转换后的文本写入到硬盘
        """
        with open(self.path+'/'+self.output, 'w') as f:
            f.write(self.content)

    def rigister(self):
        rules_func = ['self.'+rule+'()' for rule in self.__dir__() if '_rules' in rule]
        for rule_func in rules_func:
            #  print(rule_func)
            exec(rule_func)

    def common_rules(self):
        """
        普通段落、强调、斜体
        """
        self.rules.append([re.compile(r'<p>(.*?)</p>', flags=re.DOTALL), r'\1'])
        self.rules.append([re.compile(r'<strong>(.*?)</strong>',
            flags=re.DOTALL), r'**\1**'])

    def code_rules(self):
        """
        行内代码和代码块
        """
        self.rules.append([re.compile(r'<code>(.*?)</code>', flags=re.DOTALL), r'\1'])
        self.rules.append([re.compile(r'<pre>(.*?)</pre>', flags=re.DOTALL), r'''\n\1\n'''])

    def list_rules(self):
        """
        列表（有序、无序）
        """
        def replacement_list(match, order=False):
            code = match.group(1)
            if order:
                # 有序列表
                for i, tmp in enumerate(re.finditer(r'<li>(.*?)</li>', code)):
                    pat = re.sub(r'<li>(.*?)</li>', r'.*?<li>(\1)</li>.*?', re.escape(tmp.group(0)))
                    code = re.sub(pat, r'{}. \1'.format(i+1), code)
            else:
                # 无序列表
                code = re.sub(r'.*?<li>(.*?)</li>.*?', r'- \1', code)
            return code

        # 无序列表
        self.rules.append([re.compile(r'<ul>(.*?)</ul>', flags=re.DOTALL), replacement_list])
        # 有序列表
        self.rules.append([re.compile(r'<ol>(.*?)</ol>', flags=re.DOTALL), partial(replacement_list, order=True)])

    def punctuation_rules(self):
        """
        标点符号（引号等）
        """
        # 单、双引号
        self.rules.append([re.compile(r'&#39;', flags=re.DOTALL), r"'"])
        self.rules.append([re.compile(r'&quot;', flags=re.DOTALL), r'"'])

    def math_rules(self):
        """
        数学符号
        """
        # 二元关系
        self.rules.append([re.compile(r'&lt;', flags=re.DOTALL), r'<'])
        self.rules.append([re.compile(r'&gt;', flags=re.DOTALL), r'>'])

    def special_rules(self):
        """
        &nbsp; html中的空格
        """
        self.rules.append([re.compile(r'&nbsp;', flags=re.DOTALL), r''])
