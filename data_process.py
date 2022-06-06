# -*- coding:utf-8 -*-
"""
@Time: 2022/03/01 20:11
@Author: KI
@File: data_process.py
@Motto: Hungry And Humble
"""
import os
import random
import pdb
import datetime

import numpy as np
from numpy import nan as NaN
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def setup_seed(seed):
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True


# 函数统计每行空值，数量超过阈值的删除
def nan_drop(dataframe, n):
    print(dataframe.count(axis=1))
    dataframe.dropna(thresh=n)
    return


def load_data():
    """
    :return:
    """
    path = os.getcwd()
    df = pd.read_excel(path + '/data/daily.xlsx')
    # 用上值补充空白值
    df.fillna(method='ffill', inplace=True)
    # 删除2000年前的数据
    data_delete = df[df['date'] < datetime.datetime(2000, 1, 1)].index
    df.drop(data_delete, inplace=True)
    # 用下值将切片数据补充完整
    df.fillna(method='bfill', inplace=True)
    return df


class MyDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


# Multivariate-MultiStep-LSTM data processing.
def nn_seq_mm(B, num):
    print('data processing...')
    dataset = load_data()
    # split
    train = dataset[:int(len(dataset) * 0.7)]
    test = dataset[int(len(dataset) * 0.7):len(dataset)]

    def process(data, batch_size):
        load = data[data.columns[1]]
        load = load.tolist()
        data = data.values.tolist()
        m, n = np.max(load), np.min(load)
        load = (load - n) / (m - n)
        seq = []
        for i in range(0, len(data) - 24 - num, num):
            train_seq = []
            train_label = []

            for j in range(i, i + 24):
                x = [load[j]]
                for c in range(2, 8):
                    x.append(data[j][c])
                train_seq.append(x)

            for j in range(i + 24, i + 24 + num):
                train_label.append(load[j])

            train_seq = torch.FloatTensor(train_seq)
            train_label = torch.FloatTensor(train_label).view(-1)
            seq.append((train_seq, train_label))

        # print(seq[-1])
        seq = MyDataset(seq)
        seq = DataLoader(dataset=seq, batch_size=batch_size, shuffle=False, num_workers=0, drop_last=True)

        return seq, [m, n]

    Dtr, lis1 = process(train, B)
    Dte, lis2 = process(test, B)

    return Dtr, Dte, lis1, lis2


# Multivariate-SingleStep-LSTM data processing.
def nn_seq_ms(B):
    print('data processing...')
    dataset = load_data()
    # split
    train = dataset[:int(len(dataset) * 0.7)]
    test = dataset[int(len(dataset) * 0.7):len(dataset)]

    def process(data, batch_size):
        index_hs300 = data[data.columns[16]]
        index_hs300 = index_hs300.tolist()
        data = data.values.tolist()
        m, n = np.max(index_hs300), np.min(index_hs300)
        index_hs300 = (index_hs300 - n) / (m - n)
        seq = []
        for i in range(len(data) - 30):
            train_seq = []
            train_label = []
            for j in range(i, i + 30):
                x = [index_hs300[j]]
                for c in range(1, 16):
                    x.append(data[j][c])
                for c in range(17, 30):
                    x.append(data[j][c])
                train_seq.append(x)
            train_label.append(index_hs300[i + 30])
            train_seq = torch.FloatTensor(train_seq)
            train_label = torch.FloatTensor(train_label).view(-1)
            seq.append((train_seq, train_label))

        # print(seq[-1])
        seq = MyDataset(seq)
        seq = DataLoader(dataset=seq, batch_size=batch_size, shuffle=False, num_workers=0, drop_last=True)

        return seq, [m, n]

    Dtr, lis1 = process(train, B)
    Dte, lis2 = process(test, B)

    return Dtr, Dte, lis1, lis2


# Univariate-SingleStep-LSTM data processing.
def nn_seq_us(B):
    print('data processing...')
    dataset = load_data()
    # split
    train = dataset[:int(len(dataset) * 0.7)]
    test = dataset[int(len(dataset) * 0.7):len(dataset)]

    def process(data, batch_size):
        load = data[data.columns[1]]
        load = load.tolist()
        data = data.values.tolist()
        m, n = np.max(load), np.min(load)
        load = (load - n) / (m - n)
        seq = []
        for i in range(len(data) - 24):
            train_seq = []
            train_label = []
            for j in range(i, i + 24):
                x = [load[j]]
                train_seq.append(x)
            # for c in range(2, 8):
            #     train_seq.append(data[i + 24][c])
            train_label.append(load[i + 24])
            train_seq = torch.FloatTensor(train_seq)
            train_label = torch.FloatTensor(train_label).view(-1)
            seq.append((train_seq, train_label))

        # print(seq[-1])
        seq = MyDataset(seq)
        seq = DataLoader(dataset=seq, batch_size=batch_size, shuffle=False, num_workers=0, drop_last=True)

        return seq, [m, n]

    Dtr, lis1 = process(train, B)
    Dte, lis2 = process(test, B)

    return Dtr, Dte, lis1, lis2


def get_mape(x, y):
    """
    :param x: true value
    :param y: pred value
    :return: mape
    """
    return np.mean(np.abs((x - y) / x))
