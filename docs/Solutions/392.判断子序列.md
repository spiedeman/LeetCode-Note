[LeetCode[392-判断子序列]](https://leetcode-cn.com/problems/is-subsequence/)

# 题目描述
给定字符串 s 和 t ，判断 s 是否为 t 的子序列。

你可以认为 s 和 t 中仅包含英文小写字母。字符串 t 可能会很长（长度 ~= 500,000），而 s 是个短字符串（长度 <=100）。

字符串的一个子序列是原始字符串删除一些（也可以不删除）字符而不改变剩余字符相对位置形成的新字符串。（例如，"ace"是"abcde"的一个子序列，而"aec"不是）。

示例 1:
s = "abc", t = "ahbgdc"

返回 true.

示例 2:
s = "axc", t = "ahbgdc"

返回 false.

后续挑战 :

如果有大量输入的 S，称作S1, S2, ... , Sk 其中 k >= 10亿，你需要依次检查它们是否为 T 的子序列。在这种情况下，你会怎样改变代码？

# 题目分析
只要在字符串`t`中能依此找到字符串`s`中的所有字符，即可返回`True`，否则返回`False`。
因此只需遍历`t`一次。

后续挑战：
若有 k 个输入待检查，则需要 k 个指针分别指向 k 个输入字符串，给出接下来要检查的 k 个字符`[S1[i1], S2[i2], ..., Sk[ik]]`。字符串 `t` 仍然只需遍历一次。

# Code
```python
def isSubsequence(self, s, t):
    """
    双指针法
    """
    i = 0
    for c in s:
        j = t[i:].find(c) + 1
        if not j:
            return False
        i += j
    return True
  
def isSubsequence(self, s, t):
    """
    递归法，耗时耗内存
    """
    if s == "":
        return True
    j = t.find(s[0]) + 1
    return j and self.isSubsequence(s[1:], t[j:])
```
