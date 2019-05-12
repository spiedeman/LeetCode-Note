import os
import sys
import re
from functools import partial

LOCAL_PATH=os.path.split(os.path.abspath(sys.argv[0]))[0]

class HTML2MARKDOWN(object):
    def __init__(self, info=dict(), output='output.md', solution_path='.'):
        self.info = info
        self.problem = ''
        self.output = solution_path+'/'+output
        self.rules = []

    def template(self):
        with open(LOCAL_PATH+'/template.md', 'r') as f:
            page = ''.join(f.readlines())

        return page
    
    def rule_apply(self, match):
        code = match.group(1)
        for rule in self.rules:
            pat, repl = rule
            code = re.sub(pat, repl, code)
        return '</pre>{}<pre>'.format(code)
        
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
        title = self.info['title_zh'].replace('-', ' ')
        content = self.info['content_zh']
        
        if not self.rules:
            self.rigister()

        # <pre></pre> 结构内的字符串不作处理
        content = '</pre>{}<pre>'.format(content)
        content = re.sub(re.compile(r'</pre>(.*?)<pre>',flags=re.DOTALL), self.rule_apply, content)
        content = re.match(re.compile(r'</pre>(.*)<pre>',flags=re.DOTALL), content).group(1)
        content = re.sub(r'(\n{3,})', r'\n\n', content)

        form = (frontend_id, title, url, status, accept_ratio, difficulty, content)
        
        self.problem = self.template().format(*form)

    def write(self):
        """
        转换后的文本写入到硬盘
        """
        # 若文件已存在，修改多半因为更新了html转markdown格式的新规则
        # 因此题目分析和相应代码部分应做保留
        if os.access(self.output, os.F_OK):
            with open(self.output, 'r') as f:
                content = ''.join(f.readlines())
                rule = re.compile(r'(## 题目分析.*$)', flags=re.DOTALL)
                reserve = re.search(rule, content).group(1)
            self.problem = re.sub(rule, reserve, self.problem)

        #  print(self.problem)
        with open(self.output, 'w') as f:
            f.write(self.problem)

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
        self.rules.append([re.compile(r'<strong>(.*?)</strong>', flags=re.DOTALL), r'**\1**'])
        self.rules.append([re.compile(r'<em>(.*?)</em>', flags=re.DOTALL), r'*\1*'])

    def code_rules(self):
        """
        行内代码和代码块
        """
        self.rules.append([re.compile(r'<code>(.*?)</code>', flags=re.DOTALL), r'`\1`'])
        #  self.rules.append([re.compile(r'<pre>(.*?)</pre>', flags=re.DOTALL), r'''\n\1\n'''])

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
        self.rules.append([re.compile(r'&ldquo;', flags=re.DOTALL), r'“'])
        self.rules.append([re.compile(r'&rdquo;', flags=re.DOTALL), r'”'])

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
        self.rules.append([re.compile(r'<br />', flags=re.DOTALL), r'\n'])
