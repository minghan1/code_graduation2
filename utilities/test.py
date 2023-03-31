# -*- coding: utf-8 -*-
# import seaborn as sns
# sns.set_style({'font.sans-serif':['simhei','Arial']})  #防止matplotlib中文乱麻

import csv
import pandas as pd
import os
import matplotlib.pyplot as plt
import sys
import main
from tqdm import tqdm
param_default_path = os.path.join('..','config_file', 'default_file', 'param_config.csv')
config_default_path =  os.path.join('..','config_file', 'default_file', 'opt_config.csv')

# 残差长度暂时不可条，因为与操作数可计算深度有关
##############################################
# 可调参数：
# 1，长度N 0
# 2，buffer数 5
# 3，dram_bw_1 6
# 4, buffer预读取数 7
# 5，输出buffer大小 4
# 6, 各个操作延迟（直接在stream_creat.py文件中指定）
# 7，加速器带宽（直接在write_buffer_controller中指定）
# 8, dram_bw_2 8

#分析dram_bw 输出buffersize两个变量与totalcycles的关系
def deal1():

    N = 65536
    buffer_num = 5
    prefetch_num = 4
    dram_bw_2 = [x for x in range(1200, 2500, 160)]
    dram_bw_1 = 1600
    mi_size = N * 60 / 1000
    output_buffer_size = [x * mi_size for x in [0.1, 0.6, 1, 3, 8, 15]]

    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    data["val"][6] = dram_bw_1
    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    color_index = 0
    label = []
    plt.subplot(121)
    for out_size in tqdm(output_buffer_size):
        data["val"][4] = out_size
        y = []
        for d in dram_bw_2:
            data["val"][8] = d
            # print(d)
            # data.to_csv(param_default_path)
            with open(param_default_path, "w") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["param", "val"])
                for i in range(data.shape[0]):
                    writer.writerow([data["param"][i], data["val"][i]])
            cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0])
        plt.plot(dram_bw_2, y, color[color_index])
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("dram_bw")
    plt.ylabel("total_cycles")
    # plt.text(x=1000,y=150000,s="out_buffer_size = 10")
    plt.legend(label)

    dram_bw_2 = [x for x in range(1200, 2500, 160)]
    plt.subplot(122)
    for out_size in tqdm(output_buffer_size):
        data["val"][4] = out_size
        y = []
        for d in dram_bw_2:
            data["val"][8] = d
            # print(d)
            # data.to_csv(param_default_path)
            with open(param_default_path, "w") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["param", "val"])
                for i in range(data.shape[0]):
                    writer.writerow([data["param"][i], data["val"][i]])
            cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0] - cycles[5])
        plt.plot(dram_bw_2, y, color[color_index])
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("dram_bw")
    plt.ylabel("total_cycles")
    # plt.text(x=1000,y=150000,s="out_buffer_size = 10")
    plt.legend(label)
    plt.show()

#分析total cycles中的各个延迟组成与输出buffer大小的关系
def deal2():
    N = 65536
    buffer_num = 5
    prefetch_num = 4
    dram_bw_1 = 1600
    dram_bw_2 = 1000
    mi_size = N * 60 / 1000
    output_buffer_size = [x * mi_size for x in [0.3, 1, 8,18,30]]
    # for ii in output_buffer_size:
    #     print ii * 1000

    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    label = ["tot", "pre", "comp", "wr_wai", "to_wb", "fin"]
    color = ['b', 'g', 'r', 'c', 'm', 'y']
    x = [x for x in range(6)]
    data["val"][6] = dram_bw_1
    data["val"][8] = dram_bw_2
    width = 1

    yy = []
    i = 0
    for out_size in output_buffer_size:
        data["val"][4] = out_size
        with open(param_default_path, "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["param", "val"])
            for i in range(data.shape[0]):
                writer.writerow([data["param"][i], data["val"][i]])
        cycles = main.run(param_default_path, config_default_path)
        yy = cycles
        for m in range(len(x)):
            x[m] = x[m] + width * 7
        t = plt.bar(x = x, height = yy, width = width,color=color)
        plt.legend(t, label)
    plt.xlabel("out_buffer_size")
    plt.show()

#分析total cycles中的各个延迟组成与输出buffer到dram带宽的关系
def deal3():
    N = 65536
    buffer_num = 5
    prefetch_num = 4
    dram_bw_1 = 1600
    dram_bw_2 = [x for x in range(500, 2200, 160)]
    output_buffer_size = 1200
    # for ii in output_buffer_size:
    #     print ii * 1000

    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    label = ["tot", "pre", "comp", "wr_wai", "to_wb", "fin"]
    color = ['b', 'g', 'r', 'c', 'm', 'y']
    x = [x for x in range(6)]
    data["val"][6] = dram_bw_1
    data["val"][4] = output_buffer_size
    width = 1

    yy = []
    i = 0
    for dram_bw in dram_bw_2:
        data["val"][8] = dram_bw
        with open(param_default_path, "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["param", "val"])
            for i in range(data.shape[0]):
                writer.writerow([data["param"][i], data["val"][i]])
        cycles = main.run(param_default_path, config_default_path)
        yy = cycles
        for m in range(len(x)):
            x[m] = x[m] + width * 7
        t = plt.bar(x=x, height=yy, width=width, color=color)
        plt.legend(t, label)
    plt.xlabel("dram_bw_2")
    plt.show()

def deal4():

    N = 65536
    buffer_num = 5
    prefetch_num = 4
    dram_bw_2 = [x for x in range(1200, 2500, 160)]
    dram_bw_1 = 1600
    mi_size = N * 60 / 1000
    output_buffer_size = [x * mi_size for x in [0.1, 0.6, 1, 3, 8, 15]]

    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    data["val"][6] = dram_bw_1
    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    color_index = 0
    label = []
    plt.subplot(121)
    for out_size in tqdm(output_buffer_size):
        data["val"][4] = out_size
        y = []
        for d in dram_bw_2:
            data["val"][8] = d
            # print(d)
            # data.to_csv(param_default_path)
            with open(param_default_path, "w") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["param", "val"])
                for i in range(data.shape[0]):
                    writer.writerow([data["param"][i], data["val"][i]])
            cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0])
        plt.plot(dram_bw_2, y, color[color_index])
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("dram_bw")
    plt.ylabel("total_cycles")
    # plt.text(x=1000,y=150000,s="out_buffer_size = 10")
    plt.legend(label)

    dram_bw_2 = [x for x in range(1200, 2500, 160)]
    plt.subplot(122)
    for out_size in tqdm(output_buffer_size):
        data["val"][4] = out_size
        y = []
        for d in dram_bw_2:
            data["val"][8] = d
            # print(d)
            # data.to_csv(param_default_path)
            with open(param_default_path, "w") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["param", "val"])
                for i in range(data.shape[0]):
                    writer.writerow([data["param"][i], data["val"][i]])
            cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0] - cycles[5])
        plt.plot(dram_bw_2, y, color[color_index])
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("dram_bw")
    plt.ylabel("total_cycles")
    # plt.text(x=1000,y=150000,s="out_buffer_size = 10")
    plt.legend(label)
    plt.show()



if __name__ == "__main__":
    print ("赫赫")
    #分析输出buffer和带宽与cycles的关系
    deal1()
    deal2()
    deal3()

    #分析输入buffer和带宽与cycles的关系

