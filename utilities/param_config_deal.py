# -*- coding: utf-8 -*-
import pandas as pd

class mem_element:
    def __init__(self):
        self.id = 0
        self.name = " "
        self.reused = False  #是否重用
        self.insram = False  #是否已经读取到register file中
        self.residueL = 0   #残差多项式长度

class ParamConfig :
    def __init__(self):
        self.polylen = 0  #多项式长度
        self.deep_len = 0 #深度上限
        self.L = 0 #残差多项式残差数
        self.Insram_size = 0 #输入sram大小
        self.Outsram_size = 0 #输出sram大小
        self.buf_num = 0
        self.dram_bw_1 = 0
        self.prefetch_buf_num = 1
        self.dram_bw_2 = 0
        self.computer_latency = 0

        self.optlen = 0 #操作个数
        self.opt1 = [] #操作数1名称
        self.opt2 = [] #操作数2名称
        self.opt1size = [] #操作数1的残差长度
        self.opt2size = [] #操作数2的残差长度
        self.opt_vector = []
        self.opt_map = {}
        #
        #操作数类型optclass
        #0：同态加
        #1：常数与密文同态乘
        #2：同态乘
        #3: BOOTSTRAPPING
        self.optcalss = 0

    #读取操作配置文件
    def read_opt_config_file(self, config_file_path):
        data = pd.read_csv(config_file_path)
        # print("data :", data)
        self.optlen = data.shape[0]
        self.optclass = list(data["opt"])
        self.opt1 = (list)(data["opt1"])
        self.opt2 = (list)(data["opt2"])
        # self.opt1size = (list)(data["opt1size"])
        # self.opt2size = (list)(data["opt2size"])

        cnt = 1 #操作数个数（算重复）
        cnt2 = 1 #不算重复

        #获得一个操作数数组
        for i in range(self.optlen):
            t1 = mem_element()
            t2 = mem_element()
            opt1 = self.opt1[i]
            opt2 = self.opt2[i]

            if (self.optclass[i] == "NTT"):
                t1.id = cnt
                t1.name = opt1
                t1.residueL = self.L
                cnt += 1

                self.opt_vector.append(t1)
                if (not (opt1 in self.opt_map.keys())):
                    self.opt_map[opt1] = cnt2
                    cnt2 += 1

            else :
                t1.id = cnt
                t1.name = opt1
                t1.residueL = self.L
                cnt += 1

                t2.id = cnt
                t2.name = opt2
                t2.residueL = self.L
                cnt += 1

                self.opt_vector.append(t1)
                self.opt_vector.append(t2)

                if (not (opt1 in self.opt_map.keys())):
                    self.opt_map[opt1] = cnt2
                    cnt2 += 1
                if (not (opt2 in self.opt_map.keys())):
                    self.opt_map[opt2] = cnt2
                    cnt2 += 1
        global tt
        tt = {}
        #对每个操作数的reused标志赋值，0表示后面不会重用，1表示后面会重用
        for i in range(len(self.opt_vector) - 1, -1, -1):
            if (self.opt_vector[i].name in tt.keys()):
                self.opt_vector[i].reused = True
            else :
                self.opt_vector[i].reused = False
                tt[self.opt_vector[i].name] = 1

        #######################
        #--DEBUG
        # for i in self.opt_vector:
        #     print(i.name)
        #print(self.opt_map)
        # print(type(data))
        # print(self.optclass, self.opt1, self.opt2)
        # for i in self.opt_vector:
        #     print(i.name, i.id, i.reused)

    #读取参数配置文件
    def read_param_config_file(self, config_file_path):
        data = pd.read_csv(config_file_path)
        self.polylen = data["val"][0]
        self.deep_len = data["val"][1]
        self.L = data["val"][2]
        self.Insram_size = data["val"][3]
        self.Outsram_size = data["val"][4]
        self.buf_num = data["val"][5]
        self.dram_bw_1 = data["val"][6]
        self.prefetch_buf_num = data["val"][7]
        self.dram_bw_2 = data["val"][8]
        self.computer_latency = data["val"][9]

        # print("polylen: ", self.polylen,"\n", \
        #       "deep_len: ", self.deep_len, "\n", \
        #       "L: ", self.L, "\n", \
        #       "Insram_size: ", self.Insram_size, "\n", \
        #       "Outsram_size: ", self.Outsram_size, "\n", \
        #       )


