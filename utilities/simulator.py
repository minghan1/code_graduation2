# -*- coding: utf-8 -*-

import  math
import time
import param_config_deal as pcd
import stream_creat as sc
import write_buffer_controller as wbc
import gol
import controller as contr
class simulator :
    def __init__(self):
        self.optlen = 0 # 同态操作次数
        self.opt1 = [] # 同态操作数
        self.opt2 = []
        self.optclass = []  # 操作种类
        self.pa = pcd.ParamConfig()
        self.sc = sc.stream_creat()
        self.controller = contr.controller()
        self.write_controller = wbc.write_buffer_controller()

        self.word_size  = 1
        self.in_buf_size_bytes = 0
        self.out_buf_size_bytes = 0
        self.input_buf_num = 0

        self.total_cycles = 0
        self.computer_cycles = 0
        self.write_wait_cycles = 0  #等输入buffer的数据准备好的时间
        self.write_to_writebuffer_cycles = 0
        self.prefetch_cycles = 0
        self.finish_cycles = 0

        self.id = 1

    # 参数初始化
    def set_param(self, word_size = 1, in_buf_size_bytes = 0, out_buf_size_bytes = 0, input_buf_num = 0, param_config = ""):
        self.in_buf_size_bytes = in_buf_size_bytes
        self.out_buf_size_bytes = out_buf_size_bytes
        self.word_size = word_size
        self.input_buf_num = input_buf_num
        self.pa = param_config
        self.total_cycles = 0


    # 整体运行框架
    def run(self):
        start_time = time.time()

        self.optlen = self.pa.optlen
        self.opt1 = self.pa.opt1
        self.opt2 = self.pa.opt2
        self.optclass = self.pa.optclass

        self.sc.set_params(self.pa.computer_latency,self.pa.computer_latency,self.pa.computer_latency)
        # 配置内存参数
        self.controller.set_params(input_buffer_num = self.input_buf_num,\
                                   input_buffer_size_bytes=self.in_buf_size_bytes, \
                                   dram_bw_1=self.pa.dram_bw_1)
        self.write_controller.set_params(bu_size = self.out_buf_size_bytes, dram_bw = self.pa.dram_bw_2)

        # 先使sram从dram中把prefetch内存部分预读x个
        x = self.pa.prefetch_buf_num
        self.controller.set_read_buf_prefetch(x)
        self.prefetch_cycles = math.ceil(x * gol.get_polylen() * self.pa.L * 1.0 / self.controller.dram_bw_1)
        ####################
        # --DEBUG -prefetch
        # vector = gol.get_all()
        # for i in self.controller.buffer_arr:
        #     print (i, vector[i - 1].name)
        # print()
        # while  len(self.controller.reused_que):
        #     t = self.controller.reused_que.pop()
        #     print (t, vector[t - 1].name)
        # print ("finish")
        # print ("---start_cycles = ", 0, " ---")
        # 遍历执行每个操作，获得运行情况
        for i in range(self.optlen):
            start_time = time.time()
            opera1 = self.opt1[i]
            opera2 = self.opt2[i]
            operaclass = self.optclass[i]

            # start_time = time.time()
            # 在执行操作之前，先把buffer的情况更新到当前周期状态
            self.controller.update_buffer(self.total_cycles)
            # end_time = time.time()
            # print("update time is ", end_time - start_time)
            #################################################
            # --DEBUG -update
            # vector = gol.get_all()
            # t = []
            # for ii in self.controller.buffer_arr:
            #     print (ii, vector[ii - 1].name)
            # print()
            # while  len(self.controller.reused_que):
            #     m = self.controller.reused_que.pop()
            #     t.append(m)
            #     print (m,vector[m - 1].name)
            # for ii in t:
            #     self.controller.reused_que.appendleft(ii)
            # print("------------")
            #
            # print
            # print
            # print(i + 1, " :", operaclass, " ", opera1, " ", opera2)
            # 判断此时该操作所需操作数是否都已经在或者部分在sram中
            # 如果有不在的，则需要等待所有操作数都存到buffer中之后再执行操作
            flag1 = False
            flag2 = False
            if(opera2 == "xx"):
                flag2 = True
            if (opera1 in self.controller.opt_sram_map.keys()):
                flag1 = self.controller.opt_sram_map[opera1]
            if (opera2 in self.controller.opt_sram_map.keys()):
                flag2 = self.controller.opt_sram_map[opera2]
            if flag1 and flag2 :
                # start_time = time.time()
                self.total_cycles = self.run_once(operaclass, opera1, opera2, i, self.total_cycles)
                # end_time = time.time()
                # print("run_once time is ", end_time - start_time)
            else :
                # print("wait ", opera1, opera2,flag1,flag2)
                cycl = self.total_cycles
                # start_time = time.time()
                self.total_cycles = self.controller.wait_buffer(opera1, opera2, flag1, flag2, self.total_cycles)
                # end_time = time.time()
                # print("wait time is ", end_time - start_time)
                self.write_wait_cycles += (self.total_cycles - cycl)
                self.total_cycles = self.run_once(operaclass, opera1, opera2, i, self.total_cycles)
            # print(i + 1, "............now_cycles.....................",self.total_cycles)
            # end_time = time.time()
            # print("once time is ", end_time - start_time)
        self.finish_cycles = self.write_controller.finish()
        self.total_cycles += self.finish_cycles
        end_time = time.time()
        # print("once time is ", end_time - start_time)
        # print ("******total_cycles*******", math.ceil(self.total_cycles + x * gol.get_polylen() * self.pa.L * 1.0 / self.controller.dram_bw))

    def run_once(self, optclass, opt1 = "", opt2 = "", cnt = 0, start_cycles = 0):
        # global end_cycles
        # self.controller.now_exe_id += 2
        # return start_cycles + 100
        #################################################
        # 整体写回dram流程为：
        # 1，计算操作执行延迟
        # 2，更新输出buffer控制器（输出buffer用双指针循环数组的形式），即更新read_ptr以及surplus_buffer_size
        # 3，写入输出数据流获得写入延迟
        # 4，返回开始时间加上延迟得到的结束时间，总延迟为从加速器读取操作数开始到所有输出存到输出buffer

        if optclass == "ADD":
            #从输入buffer获得两个待操作数
            self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
            self.id += 2
            self.controller.now_exe_id = self.id
            #获得加法计算延迟并更新输出buffer
            computer_latency_cycles = self.sc.add_latency()
            start_time = time.time()
            self.write_controller.update_write_buffer(start_cycles + computer_latency_cycles)
            # 获取输出流矩阵
            # print (self.pa.L,gol.get_polylen(),self.write_controller.buffer_bw)
            stream_mat_output = self.sc.add_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            write_latency = self.write_controller.service_memory_requests(stream_mat_output, start_cycles + computer_latency_cycles)
            # end_time = time.time()
            # print("service time is ", end_time - start_time)
            lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
            lat1 = write_latency[0] + write_latency[1] - lat2
            self.write_to_writebuffer_cycles += lat1
            # self.computer_cycles += computer_latency_cycles + lat2
            self.computer_cycles += computer_latency_cycles
            return start_cycles + computer_latency_cycles + write_latency[0] + write_latency[1]

        if optclass == "MUL":
            #从输入buffer获得两个待操作数
            self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
            self.id += 2
            self.controller.now_exe_id = self.id
            #获得加法计算延迟并更新输出buffer
            computer_latency_cycles = self.sc.mult_latency()
            self.write_controller.update_write_buffer(start_cycles + computer_latency_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.mult_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            write_latency = self.write_controller.service_memory_requests(stream_mat_output, start_cycles + computer_latency_cycles)

            lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
            lat1 = write_latency[0] + write_latency[1] - lat2
            self.write_to_writebuffer_cycles += lat1
            # self.computer_cycles += computer_latency_cycles + lat2
            self.computer_cycles += computer_latency_cycles
            return start_cycles + computer_latency_cycles + write_latency[0] + write_latency[1]

        if optclass == "NTT":
            #从输入buffer获得两个待操作数
            self.controller.get_opt(1, [opt1],[self.id])
            self.id += 1
            self.controller.now_exe_id = self.id
            #获得加法计算延迟并更新输出buffer
            computer_latency_cycles = self.sc.ntt_latency()
            self.write_controller.update_write_buffer(start_cycles + computer_latency_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.ntt_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            write_latency = self.write_controller.service_memory_requests(stream_mat_output, start_cycles + computer_latency_cycles)

            lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
            lat1 = write_latency[0] + write_latency[1] - lat2
            self.write_to_writebuffer_cycles += lat1
            # self.computer_cycles += computer_latency_cycles + lat2
            self.computer_cycles += computer_latency_cycles
            return start_cycles + computer_latency_cycles + write_latency[0] + write_latency[1]