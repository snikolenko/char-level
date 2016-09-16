# coding:utf-8

import pandas as pd
import re
from pymystem3.mystem import Mystem
from functools import lru_cache

mystem = Mystem()


@lru_cache(maxsize=100000)
def lemmatize_line(w):
    lemmatized = mystem.lemmatize(w)
    return " ".join(lemmatized).strip()


def normalize_text(s, use_denumberization=False):
    """
    Преобразование текста перед one-hot-encoding
    :param s: initial text for analyzing
    :param use_denumberization: is False by default,
                                because there are improtant predictor numbers such as short phone numbers
    :return: prepared text
    """
    s = re.sub(u"\s+", u" ", re.sub(u"[^A-Za-zА-Яа-я0-9 ]+", u" ", s))
    s = u" ".join(map(lambda x: lemmatize_line(x), s.split(" "))).lower()

    if use_denumberization:
        return re.sub(u"\d+", u"NUMBER", s)
    else:
        return s


with open("data/ok/ok_user_train.csv") as f:
    df = pd.read_csv(f)
    print("Data read", f)
    # df.ix[:, 4] = df.ix[:, 4].map(lambda x: normalize_text((x))) #.decode("utf-8"))))
    line_len = len(list(df.ix[:, 4]))
    i = 0
    collector = []

    for line in list(df.ix[:, 4]):
        collector.append(normalize_text(line))
        if i % 100 == 0:
            print(i, "/", line_len)
        i += 1

    df.ix[:, 4] = collector

    df.to_csv("data/ok/ok_user_train_normalized.csv")

quit()

with open("data/ok/ok_user_test.csv") as f:
    df = pd.read_csv(f)
    print("Data read", f)
    df.ix[:, 4] = df.ix[:, 4].map(lambda x: normalize_text((x)))  # .decode("utf-8"))))
    df.to_csv("data/ok/ok_user_test_normalized.csv")

with open("data/ok/ok_train.csv") as f:
    df = pd.read_csv(f)
    print("Data read", f)
    df.ix[:, 4] = df.ix[:, 4].map(lambda x: normalize_text((x)))  # .decode("utf-8"))))
    df.to_csv("data/ok/ok_train_normalized.csv")

with open("data/ok/ok_test.csv") as f:
    df = pd.read_csv(f)
    print("Data read", f)
    df.ix[:, 4] = df.ix[:, 4].map(lambda x: normalize_text((x)))  # .decode("utf-8"))))
    df.to_csv("data/ok/ok_test_normalized.csv")
