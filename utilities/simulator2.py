# -*- coding: utf-8 -*-

#比simulator多考虑了 输入buffer的每一个buffer的维护和流水线
#要求计算延迟小于一个密文大小除以buffer_bw

import  math
import time
import param_config_deal as pcd

import computer.stream_creat as sc
import memory.write_buffer_controller as wbc
import gol
from memory import controller as contr
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
        self.read_stall_cycles = 0  #等输入buffer的数据准备好的时间
        self.write_to_writebuffer_cycles = 0
        self.prefetch_cycles = 0
        self.finish_cycles = 0
        self.minimum_cycles = 0

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
                                   input_buffer_size_bytes=self.in_buf_size_bytes,\
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
            opera3 = self.pa.opt3[i]
            operaclass = self.optclass[i]

            # start_time = time.time()
            # 在执行操作之前，先把buffer的情况更新到当前周期状态
            self.controller.update_buffer(self.total_cycles)
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
            # print(i + 1, " :", operaclass, " ", opera1, " ", opera2, " ",opera3," " ,self.controller.now_exe_id,self.controller.now_id)
            flag1 = False
            flag2 = False
            if(opera2 == "xx"):
                flag2 = True
            if (opera1 in self.controller.opt_sram_map.keys()):
                flag1 = self.controller.opt_sram_map[opera1]
            if (opera2 in self.controller.opt_sram_map.keys()):
                flag2 = self.controller.opt_sram_map[opera2]
            if flag1 and flag2 :
                self.total_cycles = self.run_once(operaclass, opera1, opera2, i, self.total_cycles)
            else :
                # print("wait ", opera1, opera2,flag1,flag2)
                if (operaclass == "CRB"):
                    cycl = self.total_cycles
                    self.total_cycles = self.controller.wait_buffer(opera1, opera2, flag1, flag2, self.total_cycles)
                    self.read_stall_cycles += (self.total_cycles - cycl)
                    self.total_cycles = self.run_once(operaclass, opera1, opera2, i, self.total_cycles)
                else:
                    self.total_cycles = self.run_once_2(operaclass, opera1, opera2,flag1,flag2,self.total_cycles,i)
            # print(i + 1, "............now_cycles.....................",self.total_cycles)
        self.finish_cycles = self.write_controller.finish()
        self.total_cycles += self.finish_cycles
        self.total_cycles += self.prefetch_cycles
        end_time = time.time()
        # print("once time is ", end_time - start_time)
        # print ("******total_cycles*******", math.ceil(self.total_cycles + x * gol.get_polylen() * self.pa.L * 1.0 / self.write_controller.dram_bw_2))

    def run_once(self, optclass, opt1 = "", opt2 = "", cnt = 0, start_cycles = 0):
        global write_latency
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

            #获得加法计算延迟并更新输出buffer
            computer_latency_cycles = self.sc.add_latency()
            self.write_controller.update_write_buffer(start_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.add_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            write_latency = [0,0]
            if not cnt:
                write_latency = self.write_controller.service_memory_requests(stream_mat_output - computer_latency_cycles,
                                                                              start_cycles + computer_latency_cycles)
            else:
                opt_vector = gol.get_all()
                flag = True
                if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                    flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                if self.controller.this_opt_buffer_valid and \
                    (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                    flag = False
                if (opt_vector[gol.get_len() + cnt].reused) and (self.controller.surplus_buffer_num.qsize() and flag):
                    write_latency[0] = self.hehe(stream_mat_output, opt_vector[gol.get_len() + cnt].id, start_cycles)
                    write_latency[1] = 0
                else:
                    write_latency = self.write_controller.service_memory_requests(stream_mat_output,
                                                                               start_cycles)

            lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
            if not cnt:
                lat2 -= computer_latency_cycles
            self.minimum_cycles += lat2
            lat1 = write_latency[0] + write_latency[1] - lat2
            self.write_to_writebuffer_cycles += lat1
            # self.computer_cycles += computer_latency_cycles + lat2
            self.computer_cycles = computer_latency_cycles

            # 从输入buffer获得两个待操作数
            self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
            self.id += 2
            self.controller.now_exe_id = self.id

            if not cnt:
                return start_cycles + write_latency[0] + write_latency[1] + computer_latency_cycles
            else:
                return start_cycles + write_latency[0] + write_latency[1]

        if optclass == "MUL":
            #获得加法计算延迟并更新输出buffer
            computer_latency_cycles = self.sc.mult_latency()
            self.write_controller.update_write_buffer(start_cycles)
            # 获取输出流矩阵quantize
            stream_mat_output = self.sc.mult_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存

            write_latency = [0,0]
            if not cnt:
                write_latency = self.write_controller.service_memory_requests(stream_mat_output - computer_latency_cycles,
                                                                                start_cycles + computer_latency_cycles)
            else:
                opt_vector = gol.get_all()
                flag = True
                if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                    flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                if self.controller.this_opt_buffer_valid and \
                    (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                    flag = False
                if (opt_vector[gol.get_len() + cnt].reused) and (self.controller.surplus_buffer_num.qsize() and flag):
                    write_latency[0] = self.hehe(stream_mat_output, opt_vector[gol.get_len() + cnt].id, start_cycles)
                    write_latency[1] = 0
                else:
                    write_latency = self.write_controller.service_memory_requests(stream_mat_output,
                                                                                  start_cycles)

            lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
            if not cnt:
                lat2 -= computer_latency_cycles
            self.minimum_cycles += lat2
            lat1 = write_latency[0] + write_latency[1] - lat2
            self.write_to_writebuffer_cycles += lat1
            # self.computer_cycles += computer_latency_cycles + lat2
            self.computer_cycles = computer_latency_cycles

            # 从输入buffer获得两个待操作数
            self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
            self.id += 2
            self.controller.now_exe_id = self.id

            if not cnt:
                return start_cycles + write_latency[0] + write_latency[1] + computer_latency_cycles
            else:
                return start_cycles + write_latency[0] + write_latency[1]

        if optclass == "NTT":
            #获得加法计算延迟并更新输出buffer
            computer_latency_cycles = self.sc.ntt_latency()
            self.write_controller.update_write_buffer(start_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.ntt_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            write_latency = [0,0]
            if not cnt:
                write_latency = self.write_controller.service_memory_requests(stream_mat_output - computer_latency_cycles,
                                                                                start_cycles + computer_latency_cycles)
            else:
                opt_vector = gol.get_all()
                flag = True
                if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                    flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                if self.controller.this_opt_buffer_valid and \
                    (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                    flag = False
                if (opt_vector[gol.get_len() + cnt].reused) and (self.controller.surplus_buffer_num.qsize() and flag):
                    write_latency[0] = self.hehe(stream_mat_output, opt_vector[gol.get_len() + cnt].id, start_cycles)
                    write_latency[1] = 0
                else:
                    write_latency = self.write_controller.service_memory_requests(stream_mat_output,
                                                                                  start_cycles)

            lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
            if not cnt:
                lat2 -= computer_latency_cycles
            self.minimum_cycles += lat2
            lat1 = write_latency[0] + write_latency[1] - lat2
            self.write_to_writebuffer_cycles += lat1
            # self.computer_cycles += computer_latency_cycles + lat2
            self.computer_cycles = computer_latency_cycles

            # 从输入buffer获得两个待操作数
            self.controller.get_opt(1, [opt1], [self.id])
            self.id += 1
            self.controller.now_exe_id = self.id

            if not cnt:
                return start_cycles + write_latency[0] + write_latency[1] + computer_latency_cycles
            else:
                return start_cycles + write_latency[0] + write_latency[1]

    #在有操作数没有完全写入读buffer的情况下，
    #根据输入流矩阵逐行读取
    def run_once_2(self,optclass, opt1,opt2,flag1,flag2,start_cycles,cnt):
        global t_cycles
        t_cycles = start_cycles
        self.controller.num = 0
        if optclass == "ADD":
            # 获得加法计算延迟并更新输出buffer
            # computer_latency_cycles = self.sc.add_latency()
            # self.write_controller.update_write_buffer(start_cycles + computer_latency_cycles)
            # t_cycles += computer_latency_cycles
            self.write_controller.update_write_buffer(start_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.add_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            if (not flag1) and (not flag2):
                if (not self.controller.this_opt_buffer_valid):
                    print ("simple wait buffer error 1!")
                    exit(0)
                read_cycles = self.controller.wait_buffer_one_opt(opt1,t_cycles)
                t_cycles += read_cycles
                self.read_stall_cycles += read_cycles
                self.write_controller.update_write_buffer(t_cycles)
                if (not self.controller.this_opt_buffer_valid):
                    print ("simple wait buffer error 2!")
                    exit(0)
                tt = t_cycles
                r_stall = self.read_stall_cycles

                opt_vector = gol.get_all()
                flag = True
                if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                    flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                if self.controller.this_opt_buffer_valid and \
                    (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                    flag = False
                if (opt_vector[gol.get_len() + cnt].reused) and (self.controller.surplus_buffer_num.qsize() and flag):
                    t_cycles = self.hehe2(stream_mat_output, opt_vector[gol.get_len() + cnt].id,
                                          start_cycles)
                else:
                    t_cycles = self.loop(stream_mat_output, t_cycles)

                lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
                self.minimum_cycles += lat2
                self.write_to_writebuffer_cycles += t_cycles - tt - lat2 - (self.read_stall_cycles - r_stall)
                self.controller.complete_one_opt()
                self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
                self.id += 2
                self.controller.now_exe_id = self.id
                self.controller.get_next_opt(self.controller.now_id)

            else:
                if (not self.controller.this_opt_buffer_valid):
                    print ("simple wait buffer error 3!")
                    exit(0)
                else:
                    tt = t_cycles
                    r_stall = self.read_stall_cycles

                    opt_vector = gol.get_all()
                    flag = True
                    if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                        flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                    if self.controller.this_opt_buffer_valid and \
                            (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                        flag = False
                    if (opt_vector[gol.get_len() + cnt].reused) and (
                            self.controller.surplus_buffer_num.qsize() and flag):
                        t_cycles = self.hehe2(stream_mat_output, opt_vector[gol.get_len() + cnt].id,
                                              start_cycles)
                    else:
                        t_cycles = self.loop(stream_mat_output, t_cycles)

                    lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
                    self.minimum_cycles += lat2
                    self.write_to_writebuffer_cycles += t_cycles - tt - lat2 - (self.read_stall_cycles - r_stall)
                    self.controller.complete_one_opt()
                    self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
                    self.id += 2
                    self.controller.now_exe_id = self.id
                    if flag2 and (not flag1):
                        self.controller.get_next_opt(self.controller.now_id + 1)
                    else:
                        self.controller.get_next_opt(self.controller.now_id)

        if optclass == "MUL":
            # 获得乘法计算延迟并更新输出buffer
            # computer_latency_cycles = self.sc.add_latency()
            # self.write_controller.update_write_buffer(start_cycles + computer_latency_cycles)
            # t_cycles += computer_latency_cycles
            self.write_controller.update_write_buffer(start_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.mult_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            if (not flag1) and (not flag2):
                if (not self.controller.this_opt_buffer_valid):
                    print ("simple wait buffer error 4!")
                    exit(0)
                read_cycles = self.controller.wait_buffer_one_opt(opt1, t_cycles)
                self.read_stall_cycles += read_cycles
                t_cycles += read_cycles
                self.write_controller.update_write_buffer(t_cycles)
                if (not self.controller.this_opt_buffer_valid):
                    print ("simple wait buffer error 5!")
                    exit(0)
                tt = t_cycles
                r_stall = self.read_stall_cycles

                opt_vector = gol.get_all()
                flag = True
                if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                    flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                if self.controller.this_opt_buffer_valid and \
                    (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                    flag = False
                if (opt_vector[gol.get_len() + cnt].reused) and (self.controller.surplus_buffer_num.qsize() and flag):
                    t_cycles = self.hehe2(stream_mat_output, opt_vector[gol.get_len() + cnt].id,
                                          start_cycles)
                else:
                    t_cycles = self.loop(stream_mat_output, t_cycles)

                lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
                self.minimum_cycles += lat2
                self.write_to_writebuffer_cycles += t_cycles - tt - lat2 - (self.read_stall_cycles - r_stall)
                self.controller.complete_one_opt()
                self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
                self.id += 2
                self.controller.now_exe_id = self.id
                self.controller.get_next_opt(self.controller.now_id)
            else:
                if (not self.controller.this_opt_buffer_valid):
                    print ("simple wait buffer error 6!")
                    exit(0)
                else:
                    tt = t_cycles
                    r_stall = self.read_stall_cycles

                    opt_vector = gol.get_all()
                    flag = True
                    if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                        flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                    if self.controller.this_opt_buffer_valid and \
                            (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                        flag = False
                    if (opt_vector[gol.get_len() + cnt].reused) and (
                            self.controller.surplus_buffer_num.qsize() and flag):
                        t_cycles = self.hehe2(stream_mat_output, opt_vector[gol.get_len() + cnt].id,
                                              start_cycles)
                    else:
                        t_cycles = self.loop(stream_mat_output, t_cycles)

                    lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
                    self.minimum_cycles += lat2
                    self.write_to_writebuffer_cycles += t_cycles - tt - lat2 - (self.read_stall_cycles - r_stall)
                    self.controller.complete_one_opt()
                    self.controller.get_opt(2, [opt1, opt2], [self.id, self.id + 1])
                    self.id += 2
                    self.controller.now_exe_id = self.id
                    if flag2 and (not flag1):
                        self.controller.get_next_opt(self.controller.now_id + 1)
                    else:
                        self.controller.get_next_opt(self.controller.now_id)

        if optclass == "NTT":
            # 获得ntt计算延迟并更新输出buffer
            # computer_latency_cycles = self.sc.add_latency()
            # self.write_controller.update_write_buffer(start_cycles + computer_latency_cycles)
            # t_cycles += computer_latency_cycles
            self.write_controller.update_write_buffer(start_cycles)
            # 获取输出流矩阵
            stream_mat_output = self.sc.ntt_creat(self.pa.L * gol.get_polylen(), self.write_controller.buffer_bw)
            # 将输出数据流矩阵写入内存
            if (not self.controller.this_opt_buffer_valid):
                print ("simple wait buffer error 7!")
                exit(0)
            else:
                tt = t_cycles
                r_stall = self.read_stall_cycles

                opt_vector = gol.get_all()
                flag = True
                if opt_vector[gol.get_len() + cnt].name in self.controller.opt_sram_map.keys():
                    flag = not self.controller.opt_sram_map[opt_vector[gol.get_len() + cnt].name]
                if self.controller.this_opt_buffer_valid and \
                    (opt_vector[gol.get_len() + cnt].name == opt_vector[self.controller.now_id - 1].name):
                    flag = False
                if (opt_vector[gol.get_len() + cnt].reused) and (self.controller.surplus_buffer_num.qsize() and flag):
                    t_cycles = self.hehe2(stream_mat_output, opt_vector[gol.get_len() + cnt].id,
                                          start_cycles)
                else:
                    t_cycles = self.loop(stream_mat_output, t_cycles)

                lat2 = math.ceil(self.pa.L * self.pa.polylen * 1.0 / self.write_controller.buffer_bw)
                self.minimum_cycles += lat2
                self.write_to_writebuffer_cycles += t_cycles - tt - lat2 - (self.read_stall_cycles - r_stall)
                self.controller.complete_one_opt()
                self.controller.get_opt(1, [opt1], [self.id])
                self.id += 1
                self.controller.now_exe_id = self.id
                self.controller.get_next_opt(self.controller.now_id)

        return t_cycles
    def loop(self,stream_mat_output, cycles):
        t_cycles = cycles

        #读写可以同时进行
        for data in range(stream_mat_output):
            read_cycles = self.controller.get_data()
            t_cycles += read_cycles
            self.read_stall_cycles += read_cycles
            write_cycles = self.write_controller.write_data(t_cycles)
            t_cycles += write_cycles
            self.write_controller.update_write_buffer(t_cycles)

            self.controller.last_size += (read_cycles + write_cycles ) * self.controller.dram_bw_1
            self.controller.last_cycles = t_cycles
        return t_cycles

    def hehe(self,stream,id,cycles):
        t_cycles = cycles
        # print("hehe")
        #读写不能同时进行
        for i in range(stream):
            t_cycles += 1 #读
            write_cycles = self.write_controller.write_data(t_cycles) #写
            t_cycles += write_cycles
            self.write_controller.update_write_buffer(t_cycles)

        opt_vector = gol.get_all()
        self.controller.reused_que.appendleft(id)
        buffer_index = self.controller.surplus_buffer_num.get()
        self.controller.buffer_arr[buffer_index - 1] = id
        self.controller.opt_sram_map[opt_vector[id - 1].name] = buffer_index

        return t_cycles - cycles

    def hehe2(self,stream_mat_output, id, cycles):
        t_cycles = cycles
        # print("hehe2")

        #读写不可以同时进行
        for data in range(stream_mat_output):
            read_cycles = self.controller.get_data()
            t_cycles += read_cycles + 1
            self.read_stall_cycles += read_cycles
            write_cycles = self.write_controller.write_data(t_cycles)
            t_cycles += write_cycles
            self.write_controller.update_write_buffer(t_cycles)

            self.controller.last_size += (read_cycles + write_cycles ) * self.controller.dram_bw_1
            self.controller.last_cycles = t_cycles

        opt_vector = gol.get_all()
        self.controller.reused_que.appendleft(id)
        buffer_index = self.controller.surplus_buffer_num.get()
        self.controller.buffer_arr[buffer_index - 1] = id
        self.controller.opt_sram_map[opt_vector[id - 1].name] = buffer_index
        return t_cycles