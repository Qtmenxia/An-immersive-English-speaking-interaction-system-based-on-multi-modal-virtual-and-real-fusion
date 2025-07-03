import numpy as np
import re
import string
from nltk.corpus import cmudict

# 初始化CMU词典
d = cmudict.dict()

def nsyl(word):
    """
    计算单词的音节数。
    :param word: 输入的单词
    :return: 音节数的列表（通常只返回第一个值）
    """
    try:
        return [len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]]
    except KeyError:
        return [0]

def syllcount(phrase):
    """
    计算短语中每个单词的音节数。
    :param phrase: 输入的短语
    :return: 音节数的列表
    """
    n = []
    phrase = [x for x in phrase if x not in (string.punctuation or string.whitespace or string.digits)]
    clean_message = ''.join(phrase)
    for w in clean_message.split(' '):
        n.append(nsyl(w)[0])
    return n

def word_length(phrase):
    """
    计算短语中每个单词的长度。
    :param phrase: 输入的短语
    :return: 单词长度的列表
    """
    n = []
    phrase = [x for x in phrase if x not in (string.punctuation or string.whitespace or string.digits)]
    clean_message = ''.join(phrase)
    for w in clean_message.split(' '):
        n.append(len(w))
    return n

def sentence_length(phrase):
    """
    计算短语中句子的平均长度（以单词数为单位）。
    :param phrase: 输入的短语
    :return: 句子的平均长度
    """
    n = []
    phrase = phrase.split('.')
    clean_message = ' '.join(phrase).strip()
    for w in clean_message.split(' '):
        if w:  # 避免空字符串
            n.append(len(w))
    return np.mean([len(s.split()) for s in phrase if s.strip()])

def LEXIE(phrase):
    """
    计算Flesch Readability Score（类似于Lexile分数）。
    :param phrase: 输入的短语
    :return: Flesch Readability Score
    """
    meansyll = np.mean(syllcount(phrase))
    sl = sentence_length(phrase)
    score = 206.835 - (1.015 * sl) - (84.6 * meansyll)
    return score

# 如果直接运行此文件，提供一个简单的命令行接口
if __name__ == "__main__":
    while True:
        phrase = input('Enter a phrase (or type "exit" to quit): ')
        if phrase.lower() in ['exit', 'quit']:
            print("Exiting...")
            break
        print('The Flesch Readability Score is: ' + str(LEXIE(phrase)))