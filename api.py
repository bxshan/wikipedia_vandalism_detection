# TODO: remove unessecary imports
import json
import os
import pickle
import random
import re
import subprocess
import sys
from os.path import dirname, isabs, join

import nltk
import numpy as np
from nltk import pos_tag, regexp_tokenize, word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from six import BytesIO
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

from datetime import *
from better_profanity import profanity
from spellchecker import SpellChecker
import string
import math

path_data = join(dirname(os.path.abspath(__file__)), 'nltk_data')
nltk.data.path.append(path_data)

localpool = dirname(dirname(__file__))
CLASS_NUM, WORD_DIFF_NUM = 4, 4  # 全局变量，代表难度分级和单词难度分级，一般来说都是一个数。

# 新添加,6月17日2024年


def read_source(n):  # reads a given txt file, moved from main.py
    filepath = n
    f = open(filepath, "r")
    txt_content = f.read()
    if (txt_content[:5] == "ERROR"):
        return []
    x = txt_content.splitlines()

    loc_metadata = x.index('-----METADATA')
    loc_added = x.index('-----ADDED')
    loc_deleted = x.index('-----DELETED')

    if ((loc_deleted - loc_added > 2) or (len(x) - loc_deleted > 2)):
        print(" === something wrong")

    txt_metadata = x[loc_metadata+1:loc_added]
    txt_added = x[loc_added+1:loc_deleted]
    txt_deleted = x[loc_deleted+1:]

    if (txt_metadata[8] == '<EMPTY>'):
        txt_metadata[8] = ''

    final_ret = [txt_metadata, txt_added, txt_deleted]

    return final_ret


def alpha_punct_ratio(words):
    # Define the set of allowed characters (alphabet, numbers, and common punctuation)
    allowed_chars = set(string.ascii_letters +
                        string.digits + string.punctuation)

    # Combine all words into a single string
    combined_text = ''.join(words)

    total_chars = len(combined_text)
    non_allowed_chars_count = 0

    for char in combined_text:
        if char not in allowed_chars:
            non_allowed_chars_count += 1

    if total_chars == 0:
        return 0  # To avoid division by zero

    return non_allowed_chars_count / total_chars


def spell_err_ratio(words):
    spell = SpellChecker()

    # Find misspelled words
    misspelled_words = spell.unknown(words)

    total_words = len(words)
    misspelled_count = len(misspelled_words)

    if total_words == 0:
        return 0  # To avoid division by zero

    return misspelled_count / total_words


def longest_consec_char_ratio(words):
    # Combine all words into a single string
    combined_text = ''.join(words)

    # Initialize variables
    max_sequence_length = 0
    current_sequence_length = 1

    # Loop through the combined text to find the longest sequence of consecutive characters
    for i in range(1, len(combined_text)):
        if combined_text[i] == combined_text[i - 1]:
            current_sequence_length += 1
        else:
            if current_sequence_length > max_sequence_length:
                max_sequence_length = current_sequence_length
            current_sequence_length = 1

    # Check last sequence
    if current_sequence_length > max_sequence_length:
        max_sequence_length = current_sequence_length

    # Calculate the ratio
    total_length = len(combined_text)
    if total_length == 0:
        return 0  # To avoid division by zero

    return max_sequence_length / total_length


def profane_ratio(words):
    total_words = len(words)
    profane_words = 0

    for word in words:
        if profanity.contains_profanity(word):
            profane_words += 1

    if total_words == 0:
        return 0  # To avoid division by zero

    return profane_words / total_words


def uppercase_ratio(strings):
    total_uppercase = 0
    total_letters = 0

    for string in strings:
        for char in string:
            if char.isalpha():
                total_letters += 1
                if char.isupper():
                    total_uppercase += 1

    if total_letters == 0:
        return 0  # To avoid division by zero

    return total_uppercase / total_letters


def time_diff(date1, date2):
  # check which date is greater to avoid days output in -ve number
    if date2 > date1:
        return (date2-date1).days
    else:
        return (date1-date2).days

# 老添加的


def load_data(listpath, label_choose={}):  # 加载数据，是下面三个加载各种数据的基函数
    with open(listpath) as f:
        lines = f.readlines()

    data = []
    for line in lines:
        path, label = line.strip().split()
        label = int(label)
        data.append([path, label])
    # print(data)
    return data


def load_train_data():
    data = load_data(join(localpool, 'pioneer_boxuan/datalists/trainlist.txt'),
                     set(range(CLASS_NUM)))
    return data


def load_test_data():
    data = load_data(join(localpool, 'pioneer_boxuan/datalists/testlist.txt'),
                     set(range(CLASS_NUM)))
    return data


def get_feats_labels(data,
                     newFeatures=None,
                     add_len=True):  # 获得特征
    # diff_use就是两种难度评级
    features = []
    labels = []
    for path, label in data:
        print("processing file " + path + "... ")
        if not (newFeatures is None):
            text = read_source(path)
            if (len(text) == 0):
                continue

            features.append([])
            for F in newFeatures:  # 遍历特征列表里每一种需要提取的特征。
                tmp_f = F(text)
                # 下面的有关对齐的讨论比较繁琐，可以简化，就可以直接理解为每次把新提取的特征缝到一起
                if not add_len:
                    if len(tmp_f) > len(features[-1]):
                        features[-1] += [0] * (len(tmp_f) - len(features[-1]))
                    features[-1] = [
                        features[-1][i] + tmp_f[i]
                        for i in range(len(features[-1]))
                    ]
                else:
                    features[-1].append(tmp_f)

        labels.append(int(label))  # label是'1'这种字符串形式的数字，注意转化。

    return features, labels


class logistic_regression():  # 逻辑回归原型。
    def __init__(self, optimizer='logistic'):
        if optimizer == 'logistic':
            self.cls = LogisticRegression(C=10000,
                                          max_iter=10000,
                                          multi_class='ovr')  # 初始化逻辑回归。
        else:
            self.cls = None

        self.x = None
        self.y = None
        self.weights = []
        self.optimizer = optimizer

    def make_data_x(self, x):
        x = np.array(x)
        if len(x.shape) == 1:
            x = np.expand_dims(x, axis=1)

        return x

    def make_data_y(self, y):
        y = np.array(y)

        return y

    def train(self, x, y):
        self.x = self.make_data_x(x)
        self.y = self.make_data_y(y)
        self.cls.fit(self.x, self.y)  # 进行拟合

    def pred(self, x):  # 做预测的函数。
        if type(x) is not np.ndarray:
            x = self.make_data_x(x)
        ret = self.cls.predict(x).tolist()

        if len(ret) == 1:
            ret = ret[0]

        return ret


def accuracy(pred, y):  # 评估准确率的函数。
    right = 0
    total = 0
    for i in range(len(pred)):
        if pred[i] == y[i]:
            right += 1
        total += 1

    acc = 1.0 * right / total
    return acc
