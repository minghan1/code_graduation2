# -*- coding: utf-8 -*-
# import seaborn as sns
# sns.set_style({'font.sans-serif':['simhei','Arial']})  #防止matplotlib中文乱麻

import numpy as np
import time
import csv
import pandas as pd
import os
import matplotlib.pyplot as plt
import sys

import gol
import main
from tqdm import tqdm
param_default_path = os.path.join('..','config_file', 'default_file', 'param_config.csv')
config_default_path =  os.path.join('..','config_file', 'default_file', 'opt_config.csv')
result_default_path = os.path.join('..','test_results')
class param:
    def __init__(self):
        self.N = 0
        self.buffer_num = 0
        self.dram_bw_1 = 0
        self.dram_bw_2 = 0
        self.prefetch_num = 0
        self.out_buffer_size = 0
        self.computer_latency = 0
    def set_params(self,N,buffer_num,dram_bw_1,dram_bw_2,prefetch_bum,\
                   out_buffer_size,conputer_latency):
        self.N = N
        self.buffer_num = buffer_num
        self.dram_bw_1 = dram_bw_1
        self.dram_bw_2 = dram_bw_2
        self.prefetch_num = prefetch_bum
        self.out_buffer_size = out_buffer_size
        self.computer_latency = conputer_latency


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
# 9, computer_latency 9

#分析dram_bw 输出buffersize两个变量与totalcycles的关系
def deal1():

    N = 65536
    buffer_num = 2
    prefetch_num = 2
    dram_bw_2 = [x for x in range(200, 1000, 100)]
    dram_bw_1 = 1200
    mi_size = N * 60 / 1000
    output_buffer_size = [x*3 for x in [1,90,400,1000,10000]]
    computer_latency = 600
    parammm = param()

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
            parammm.set_params(N, buffer_num, 1200-d, d, prefetch_num, out_size, computer_latency)
            cycles = main.run(param_default_path, config_default_path, parammm)
            # print(d)
            # data.to_csv(param_default_path)
            # with open(param_default_path, "w") as csvfile:
            #     writer = csv.writer(csvfile)
            #     writer.writerow(["param", "val"])
            #     for i in range(data.shape[0]):
            #         writer.writerow([data["param"][i], data["val"][i]])
            # cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0])
        plt.plot(dram_bw_2, y, color[color_index])
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("dram_bw")
    plt.ylabel("total_cycles")
    # plt.text(x=1000,y=150000,s="out_buffer_size = 10")
    plt.legend(label)

    # dram_bw_2 = [x for x in range(600, 2500, 160)]
    # plt.subplot(122)
    # for out_size in tqdm(output_buffer_size):
    #     data["val"][4] = out_size
    #     y = []
    #     for d in dram_bw_2:
    #         data["val"][8] = d
    #         # print(d)
    #         # data.to_csv(param_default_path)
    #         parammm.set_params(N, buffer_num, dram_bw_1, d, prefetch_num, out_size, computer_latency)
    #         cycles = main.run(param_default_path, config_default_path,parammm)
    #         y.append(cycles[0] - cycles[5])
    #     plt.plot(dram_bw_2, y, color[color_index])
    #     strr = "outbuffersize " + str(out_size) + "k"
    #     label.append(strr)
    #     color_index = (color_index + 1) % len(color)
    # plt.xlabel("dram_bw")
    # plt.ylabel("total_cycles")
    # # plt.text(x=1000,y=150000,s="out_buffer_size = 10")
    # plt.legend(label)
    result_default_path_2 = os.path.join(result_default_path, "deal1.png")
    plt.savefig(result_default_path_2,dpi = 600, bbox_inches='tight')
    plt.show()

#分析total cycles中的各个延迟组成与输出buffer大小的关系
def deal2():
    N = 65536
    buffer_num = 8
    prefetch_num = 8
    dram_bw_1 = 600
    dram_bw_2 = 500
    mi_size = N * 60 / 1000
    output_buffer_size = [x*3 for x in [10,100,1000,5000,10000]]
    # for ii in output_buffer_size:
    #     print ii * 1000
    parammm = param()
    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    label = ["tot", "mini", "pre", "comp", "re_stall", "wr_stall", "fin"]
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    x = np.arange(7)
    data["val"][6] = dram_bw_1
    data["val"][8] = dram_bw_2
    width = 1

    com_lat_str = []
    for u in output_buffer_size:
        com_lat_str.append(str(u))

    yy = []
    i = 0
    for out_size in output_buffer_size:
        data["val"][4] = out_size
        parammm.set_params(N,buffer_num,dram_bw_1,dram_bw_2,prefetch_num,out_size,conputer_latency=600)
        # with open(param_default_path, "w") as csvfile:
        #     writer = csv.writer(csvfile)
        #     writer.writerow(["param", "val"])
        #     for i in range(data.shape[0]):
        #         writer.writerow([data["param"][i], data["val"][i]])
        cycles = main.run(param_default_path, config_default_path,parammm)
        yy = cycles
        # yy[1] = N * 60 * gol.get_optlen() / dram_bw_2 + yy[2]
        for m in range(len(x)):
            x[m] = x[m] + width * 8
        t = plt.bar(x = x, height = yy, width = width,color=color)
        plt.legend(t, label)
    plt.xlabel("out_buffer_size")
    x = np.arange(len(output_buffer_size))
    for i in range(x.size):
        x[i] = i * width * 8 + 6 * width
    plt.xticks(x + width * 3, com_lat_str)
    result_default_path_2 = os.path.join(result_default_path, "deal2.png")
    plt.savefig(result_default_path_2,dpi = 600, bbox_inches='tight')
    plt.show()

#分析total cycles中的各个延迟组成与输出buffer到dram带宽的关系
def deal3():
    N = 65536
    buffer_num = 8
    prefetch_num = 8
    dram_bw_1 = 1200
    dram_bw_2 = [x for x in range(100, 1200, 100)]
    output_buffer_size = 1200
    # for ii in output_buffer_size:
    #     print ii * 1000
    computer_latency = 600
    parammm = param()

    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    label = ["tot", "mini", "pre", "comp", "re_stall", "wr_stall", "fin"]
    color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    x = np.arange(7)
    data["val"][6] = dram_bw_1
    data["val"][4] = output_buffer_size
    width = 1

    com_lat_str = []
    for u in dram_bw_2:
        com_lat_str.append(str(u))

    yy = []
    i = 0
    for dram_bw in dram_bw_2:
        data["val"][8] = dram_bw
        parammm.set_params(N, buffer_num, 1200 - dram_bw, dram_bw, prefetch_num, output_buffer_size,
                           conputer_latency=computer_latency)
        cycles = main.run(param_default_path, config_default_path, parammm)
        # with open(param_default_path, "w") as csvfile:
        #     writer = csv.writer(csvfile)
        #     writer.writerow(["param", "val"])
        #     for i in range(data.shape[0]):
        #         writer.writerow([data["param"][i], data["val"][i]])
        # cycles = main.run(param_default_path, config_default_path)
        yy = cycles
        for m in range(len(x)):
            x[m] = x[m] + width * 8
        t = plt.bar(x=x, height=yy, width=width, color=color)
        plt.legend(t, label)
    plt.xlabel("dram_bw_2")
    x = np.arange(len(dram_bw_2))
    for i in range(x.size):
        x[i] = i * width * 8 + 6 * width
    plt.xticks(x + width * 3, com_lat_str)
    result_default_path_2 = os.path.join(result_default_path, "deal3.png")
    plt.savefig(result_default_path_2,dpi = 600, bbox_inches='tight')
    plt.show()

#三个片上buffer变量以及计算延迟与total cycles的关系
def deal4():

    N = 65536
    buffer_num = np.array([2, 5, 9, 15])
    prefetch_num = np.array([[2],[2,4],[2,4,9],[2,5,9,15]])

    dram_bw_2 = 1000
    dram_bw_1 = 1200
    mi_size = N * 60 / 1000
    output_buffer_size = [x * mi_size for x in [0.1, 0.3, 0.7, 1, 3]]
    computer_latency = [x for x in [10,50,100,200,300]]

    parammm = param()
    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    # data["val"][5] = buffer_num
    # data["val"][7] = prefetch_num
    data["val"][6] = dram_bw_1
    data["val"][8] = dram_bw_2
    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    ii = 1
    fi = plt.figure(1)
    label = []
    for out_size in output_buffer_size:
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
    for buf_num in tqdm(buffer_num):
        data["val"][5] = buf_num
        j = 1
        for pre_num in tqdm(prefetch_num[ii - 1]):
            data["val"][7] = pre_num
            color_index = 0
            # print ("buf_num ", buf_num, "pre_num", pre_num, (ii - 1) * 4 + j)
            plt.subplot(4,4,(ii - 1) * 4 + j)
            for out_size in output_buffer_size:
                data["val"][4] = out_size
                y = []


                for com_lat in computer_latency:
                    start_time = time.time()
                    data["val"][8] = com_lat
                    parammm.set_params(N, buf_num, dram_bw_1, dram_bw_2, pre_num, out_size, com_lat)
                    # with open(param_default_path, "w") as csvfile:
                    #     writer = csv.writer(csvfile)
                    #     writer.writerow(["param", "val"])
                    #     for i in range(data.shape[0]):
                    #         writer.writerow([data["param"][i], data["val"][i]])
                    cycles = main.run(param_default_path, config_default_path,parammm)
                    y.append(cycles[0])
                    end_time = time.time()
                    # print("once_time is ", end_time - start_time)
                plt.plot(computer_latency, y, color[color_index])
                if (j == 1):
                    strr = "buffer_num = " + str(buf_num)
                    plt.ylabel(strr, color='r')
                if (ii == 4):
                    strr = "prefetch_num = " + str(pre_num)
                    plt.xlabel(strr,color='r')
                color_index = (color_index + 1) % len(color)

            j += 1
        ii += 1
    fi.legend(label)
    # plt.xlabel("computer_latency")
    fi.suptitle("x_axis is computer_latency", fontsize=20)
    result_default_path_2 = os.path.join(result_default_path, "deal4.png")
    plt.savefig(result_default_path_2)
    plt.show()



#分析total cycles中的各个延迟组成与computer_latency大小的关系
def deal5():
    N = 65536
    buffer_num = 9
    prefetch_num = 9
    dram_bw_1 = 1200
    dram_bw_2 = 1000
    mi_size = N * 60 / 1000
    output_buffer_size = 120000
    computer_latency = [x for x in [10,50,100,200,300]]

    com_lat_str = []
    for u in computer_latency:
        com_lat_str.append(str(u))

    parammm = param()
    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    data["val"][5] = buffer_num
    data["val"][7] = prefetch_num
    label = ["tot", "mini","pre", "comp", "re_stall", "wr_stall", "fin"]
    color = ['b', 'g', 'r', 'c', 'm', 'y','k']
    x = np.arange(7)
    data["val"][6] = dram_bw_1
    data["val"][8] = dram_bw_2
    width = 1

    i = 0
    for com_lat in computer_latency:
        parammm.set_params(N,buffer_num,dram_bw_1,dram_bw_2,prefetch_num,output_buffer_size,conputer_latency=com_lat)
        cycles = main.run(param_default_path, config_default_path,parammm)
        yy = cycles
        # print ("set_lat",com_lat, "com_sum_lat",cycles[2])
        for m in range(len(x)):
            x[m] = x[m] + width * 7
        t = plt.bar(x = x, height = yy, width = width,color=color)
        plt.legend(t, label)
    plt.xlabel("computer_latency")
    result_default_path_2 = os.path.join(result_default_path, "deal5.png")
    x = np.arange(6)
    for i in range(x.size):
        x[i] = i * width * 7 + 6 * width
    plt.xticks(x + width * 3,com_lat_str)
    plt.savefig(result_default_path_2)
    plt.show()


def deal6():
    N = 65536
    buffer_num = np.array([2, 5, 9, 15])
    prefetch_num = np.array([[2], [2, 4], [2, 4, 9], [2, 5, 9, 15]])

    dram_bw_2 = [x for x in range(100, 1200, 100)]
    dram_bw_1 = 1200
    mi_size = N * 60 / 1000
    output_buffer_size = [x * mi_size for x in [0.1, 0.3, 0.8,1,3,8]]
    computer_latency = 50

    parammm = param()
    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    # data["val"][5] = buffer_num
    # data["val"][7] = prefetch_num
    data["val"][6] = dram_bw_1
    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    ii = 1
    fi = plt.figure(1)
    label = []
    for out_size in output_buffer_size:
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
    for buf_num in tqdm(buffer_num):
        data["val"][5] = buf_num
        j = 1
        for pre_num in tqdm(prefetch_num[ii - 1]):
            data["val"][7] = pre_num
            color_index = 0
            # print ("buf_num ", buf_num, "pre_num", pre_num, (ii - 1) * 4 + j)
            plt.subplot(4, 4, (ii - 1) * 4 + j)
            for out_size in output_buffer_size:
                data["val"][4] = out_size
                y = []

                for dram_2 in dram_bw_2:
                    start_time = time.time()
                    parammm.set_params(N, buf_num, 1200-dram_2, dram_2, pre_num, out_size, computer_latency)
                    # with open(param_default_path, "w") as csvfile:
                    #     writer = csv.writer(csvfile)
                    #     writer.writerow(["param", "val"])
                    #     for i in range(data.shape[0]):
                    #         writer.writerow([data["param"][i], data["val"][i]])
                    cycles = main.run(param_default_path, config_default_path, parammm)
                    y.append(cycles[0] - N * 60 * gol.get_optlen() / dram_2 + cycles[2])
                    end_time = time.time()
                    # print("once_time is ", end_time - start_time)
                plt.plot(dram_bw_2, y, color[color_index])
                if (j == 1):
                    strr = "buffer_num = " + str(buf_num)
                    plt.ylabel(strr, color='r')
                if (ii == 4):
                    strr = "prefetch_num = " + str(pre_num)
                    plt.xlabel(strr, color='r')
                color_index = (color_index + 1) % len(color)

            j += 1
        ii += 1
    fi.legend(label)
    # plt.xlabel("computer_latency")
    fi.suptitle("x_axis is dram_bw_2", fontsize=20)
    result_default_path_2 = os.path.join(result_default_path, "deal6.png")
    plt.savefig(result_default_path_2)
    plt.show()

def deal7():

    N = 65536
    buffer_num = [x for x in [2,5,8,13,18,23]]
    prefetch_num = 2
    dram_bw_2 = [x for x in range(100, 1200, 100)]
    dram_bw_1 = 1200
    mi_size = N * 60 / 1000
    output_buffer_size = mi_size * 1
    computer_latency = 600
    parammm = param()

    data = pd.read_csv(param_default_path)

    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    color_index = 0
    label = []
    plt.subplot(121)
    for d in tqdm(dram_bw_2):
        y = []
        for buf_num in buffer_num:

            parammm.set_params(N, buf_num, 1200- d, d, prefetch_num, output_buffer_size, computer_latency)
            cycles = main.run(param_default_path, config_default_path, parammm)
            # print(d)
            # data.to_csv(param_default_path)
            # with open(param_default_path, "w") as csvfile:
            #     writer = csv.writer(csvfile)
            #     writer.writerow(["param", "val"])
            #     for i in range(data.shape[0]):
            #         writer.writerow([data["param"][i], data["val"][i]])
            # cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0] - N * 60 * gol.get_optlen() / d + cycles[2])
        plt.plot(buffer_num, y, color[color_index])
        strr = "dram_bw_2 " + str(d)
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("buf_num")
    plt.ylabel("total_cycles")
    plt.legend(label)
    result_default_path_2 = os.path.join(result_default_path, "deal7.png")
    plt.savefig(result_default_path_2)
    plt.show()


def deal8():
    N = 65536
    buffer_num = np.array([2, 5, 9, 15])
    prefetch_num = np.array([[2], [2, 4], [2, 4, 9], [2, 5, 9, 15]])

    dram_bw_2 = [x for x in range(200, 1000, 100)]
    dram_bw_1 = 1200
    mi_size = N * 60 / 1000
    output_buffer_size = [x*3 for x in [1,90,400,1000,10000]]
    computer_latency = 50

    parammm = param()
    data = pd.read_csv(param_default_path)
    data["val"][0] = N
    # data["val"][5] = buffer_num
    # data["val"][7] = prefetch_num
    data["val"][6] = dram_bw_1
    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    ii = 1
    fi = plt.figure(1)
    label = []
    for out_size in output_buffer_size:
        strr = "outbuffersize " + str(out_size) + "k"
        label.append(strr)
    for buf_num in tqdm(buffer_num):
        data["val"][5] = buf_num
        j = 1
        for pre_num in tqdm(prefetch_num[ii - 1]):
            data["val"][7] = pre_num
            color_index = 0
            # print ("buf_num ", buf_num, "pre_num", pre_num, (ii - 1) * 4 + j)
            plt.subplot(4, 4, (ii - 1) * 4 + j)
            for out_size in output_buffer_size:
                data["val"][4] = out_size
                y = []

                for dram_2 in dram_bw_2:
                    # print buf_num, pre_num, out_size, dram_2
                    start_time = time.time()
                    parammm.set_params(N, buf_num, 1200 - dram_2, dram_2, pre_num, out_size, computer_latency)
                    # with open(param_default_path, "w") as csvfile:
                    #     writer = csv.writer(csvfile)
                    #     writer.writerow(["param", "val"])
                    #     for i in range(data.shape[0]):
                    #         writer.writerow([data["param"][i], data["val"][i]])
                    cycles = main.run(param_default_path, config_default_path, parammm)
                    y.append(cycles[0])
                    end_time = time.time()
                    # print("once_time is ", end_time - start_time)
                plt.plot(dram_bw_2, y, color[color_index])
                if (j == 1):
                    strr = "buffer_num = " + str(buf_num)
                    plt.ylabel(strr, color='r')
                if (ii == 4):
                    strr = "prefetch_num = " + str(pre_num)
                    plt.xlabel(strr, color='r')
                color_index = (color_index + 1) % len(color)

            j += 1
        ii += 1
    fi.legend(label)
    # plt.xlabel("computer_latency")
    fi.suptitle("x_axis is dram_bw_2", fontsize=20)
    result_default_path_2 = os.path.join(result_default_path, "deal8.png")
    plt.savefig(result_default_path_2,dpi = 600, bbox_inches='tight')
    plt.show()

def deal9():

    N = 65536
    buffer_num = [x for x in [2,5,8,13,18,23]]
    prefetch_num = 2
    dram_bw_2 = [x for x in range(100, 800, 100)]
    dram_bw_1 = 1200
    mi_size = N * 60 / 1000
    output_buffer_size = 1200
    computer_latency = 600
    parammm = param()

    data = pd.read_csv(param_default_path)

    color = ['b.-', 'g.-', 'r.-', 'c.-', 'm.-', 'y.-', 'k.-']
    color_index = 0
    label = []
    plt.subplot(121)
    for d in tqdm(dram_bw_2):
        y = []
        for buf_num in buffer_num:

            parammm.set_params(N, buf_num, 1200 - d, d, prefetch_num, output_buffer_size, computer_latency)
            cycles = main.run(param_default_path, config_default_path, parammm)
            # print(d)
            # data.to_csv(param_default_path)
            # with open(param_default_path, "w") as csvfile:
            #     writer = csv.writer(csvfile)
            #     writer.writerow(["param", "val"])
            #     for i in range(data.shape[0]):
            #         writer.writerow([data["param"][i], data["val"][i]])
            # cycles = main.run(param_default_path, config_default_path)
            y.append(cycles[0])
        plt.plot(buffer_num, y, color[color_index])
        strr = "dram_bw_2 " + str(d)
        label.append(strr)
        color_index = (color_index + 1) % len(color)
    plt.xlabel("buf_num")
    plt.ylabel("total_cycles")
    plt.legend(label)
    result_default_path_2 = os.path.join(result_default_path, "deal9.pdf")
    plt.savefig(result_default_path_2,dpi = 600, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    print ("赫赫")
    #分析输出buffer和带宽与cycles的关系
    # deal1()
    deal2()
    # deal3()
    #
    # deal4()
    # deal5()
    # deal6()
    # deal7()
    # deal8()
    # deal9()


