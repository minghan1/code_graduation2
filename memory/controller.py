# -*- coding: utf-8 -*-
import gol
import math
import sys
if sys.version > '3':
    import queue as Queue
else :
    import Queue
from collections import  deque

class controller:
    def __init__(self):
        self.input_buffer_num = 0
        self.input_buffer_bytes = 0
        self.opt_vector = []
        self.reused_que = deque() # 目前在重用的操作数队列，用于维护踢出还在片上的的最早的重用操作数
        self.buffer_arr = []  # 记录每个输入buffer里面的操作数id
        self.surplus_buffer_num = Queue.Queue()  #空闲buffer队列
        self.now_exe_id = 0  #接下来 加速器PL核要从buffer中读取哪一个操作数
        self.buffer_bw = 2048

        # 如果一个操作数的名字不在opt_sram_map.keys()中，那么该操作数一定在片上缓存
        # 如果在，并且对于的值为True，那么该操作数在片上缓存中
        self.opt_sram_map = {} # 记录操作数是否在片上  key:操作数名  value: buffer index

        # 下面的"上一次"对应着simulator中对update_buffer和wait_buffer的调用
        # 下面变量都是针对的now_id这个操作数
        self.last_cycles = 0  # 上一次更新buffer的时间点
        self.dram_bw_1 = 0 # dram的带宽(elements/cycle)
        self.dram_bw_2 = 0
        self.now_id = 1  # 上一次写到了哪一个操作数
        self.last_size = 0 # now_id这个操作数上次写了多少
        self.this_opt_size = 0#要写的操作数的大小
        self.this_opt_buffer_valid = False #当前这个要写的操作数是否已经指定buffer
        self.this_opt_buffer_index = 1
        self.num = 0  #当前buffer被读走多少数据了


    def set_params(self, input_buffer_num = 0, input_buffer_size_bytes = 0,dram_bw_1 = 0):
        self.input_buffer_num = input_buffer_num
        self.input_buffer_bytes = input_buffer_size_bytes
        # self.output_buffer_size = output_buffer_size
        self.opt_vector = gol.get_all()
        self.dram_bw_1 = dram_bw_1
        for i in range(1, input_buffer_num + 1):
            self.surplus_buffer_num.put(i)
        self.now_exe_id = 1
        for i in range(input_buffer_num):
            self.buffer_arr.append(0)

    # 在开始运行加速器之前先把buffer预取x个
    def set_read_buf_prefetch(self, x = 0):
        # print("set_prefetch")
        self.opt_vector = gol.get_all()
        i = 0  # 指向buffer_arr
        j = 0  # 指向opt_arr
        while ((i < self.input_buffer_num) and (i < x)):
            if (self.opt_vector[j].name in self.opt_sram_map.keys()):
                j += 1
                continue
            if(j >= len(self.opt_vector)):
                break
            self.opt_vector[j].insram = True
            # self.buffer_arr.append(self.opt_vector[j].id)
            self.buffer_arr[i] = self.opt_vector[j].id
            self.opt_sram_map[self.opt_vector[j].name] = self.surplus_buffer_num.get()
            # self.now_id += 1
            if (self.opt_vector[j].reused):
                self.reused_que.appendleft(self.opt_vector[j].id)
            gol.reset_all_value(self.opt_vector)
            i += 1
            j += 1
            self.opt_vector = gol.get_all()

        #获得下一个要读取的操作数
        self.get_next_opt(self.now_id - 1)
        # while(self.opt_vector[j].name in self.opt_sram_map.keys()):
        #     j += 1
        #     if (j >= len(self.opt_vector)):
        #         break
        # self.now_id = j + 1
        # if (self.now_id > gol.get_len()):
        #     return
        # if(self.surplus_buffer_num.qsize()):
        #     print("error!!!!!!")
        #     # self.opt_sram_map[self.opt_vector[self.now_id - 1].name] = self.surplus_buffer_num.get()
        #     # self.this_opt_buffer_valid = True
        #     # self.buffer_arr[self.opt_sram_map[self.opt_vector[self.now_id - 1].name]] = self.now_id
        # else:
        #     self.last_size = 0
        #     self.last_cycles = 0
        #     self.this_opt_buffer_valid = False
        #     self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()
        # gol.reset_all_value(self.opt_vector)
        # print ("prefetch finish")


    # 将buffer的情况更新到now_cycles
    def update_buffer(self, now_cycles = 0):
        # 数据已经全部读完了
        if (self.now_id > gol.get_len()):
            self.last_cycles = now_cycles
            return

        sub_cycles = now_cycles - self.last_cycles
        self.last_cycles = now_cycles
        write_bytes = self.dram_bw_1 * sub_cycles    #应该是write_element_nums，表示最多可以从dram中读取多少个element(残差之后的数)
        if (not write_bytes):
            return
        self.opt_vector = gol.get_all()

        # 读取dram中的数据到buffer中， write_bytes大于等于当前要读操作数剩余大小则完成该操作数读取，小于则将write_bytes读完

        while(True):
            if(sub_cycles <= 0):
                break
            if(self.now_id > gol.get_len()):
                break
            write_bytes = self.dram_bw_1 * sub_cycles
            this_opt_need_cycles = math.ceil((1.0 * self.this_opt_size - self.last_size) / self.dram_bw_1)
            if (self.this_opt_buffer_valid):
                # buffer_index = self.opt_sram_map[self.opt_vector[self.now_id - 1].name]
                if (this_opt_need_cycles <= sub_cycles):
                    # 完成这个操作数的读取
                    sub_cycles -= this_opt_need_cycles
                    self.opt_vector[self.now_id - 1].insram = True
                    self.opt_sram_map[self.opt_vector[self.now_id - 1].name] = self.this_opt_buffer_index
                    self.buffer_arr[self.this_opt_buffer_index - 1] = self.now_id
                    if (self.opt_vector[self.now_id - 1].reused):
                        self.reused_que.appendleft(self.opt_vector[self.now_id - 1].id)
                    gol.reset_all_value(self.opt_vector)

                    # 获得下一个要读取的操作数
                    self.get_next_opt(self.now_id)
                else:
                    self.last_size = self.last_size + write_bytes
                    break
            else:
                if (self.surplus_buffer_num.qsize()):
                    self.this_opt_buffer_index = self.surplus_buffer_num.get()
                    self.this_opt_buffer_valid = True
                    if (this_opt_need_cycles <= sub_cycles):
                        # 完成这个操作数的读取
                        sub_cycles -= this_opt_need_cycles
                        self.opt_vector[self.now_id - 1].insram = True
                        self.opt_sram_map[self.opt_vector[self.now_id - 1].name] = self.this_opt_buffer_index
                        self.buffer_arr[self.this_opt_buffer_index - 1] = self.now_id
                        if (self.opt_vector[self.now_id - 1].reused):
                            self.reused_que.appendleft(self.opt_vector[self.now_id - 1].id)
                        gol.reset_all_value(self.opt_vector)
                        # 获得下一个要读取的操作数
                        self.get_next_opt(self.now_id)
                    else:
                        self.last_size = self.last_size + write_bytes
                        break
                else:
                    if(not len(self.reused_que)):
                        break
                    temp = []
                    flag = True
                    while(len(self.reused_que)):
                        re_id = self.reused_que.pop()
                        if (not self.check(re_id, self.now_exe_id, self.now_id, self.opt_vector)):
                            self.this_opt_buffer_valid = True
                            self.this_opt_buffer_index = self.opt_sram_map[self.opt_vector[re_id - 1].name]

                            # 踢出re_id这个操作数
                            self.opt_sram_map[self.opt_vector[re_id - 1].name] = 0
                            self.buffer_arr[self.this_opt_buffer_index - 1] = 0

                            if (this_opt_need_cycles <= sub_cycles):
                                # 完成这个操作数的读取
                                sub_cycles -= this_opt_need_cycles
                                self.opt_vector[self.now_id - 1].insram = True
                                self.opt_sram_map[self.opt_vector[self.now_id - 1].name] = self.this_opt_buffer_index
                                self.buffer_arr[self.this_opt_buffer_index -1] = self.now_id
                                if (self.opt_vector[self.now_id - 1].reused):
                                    self.reused_que.appendleft(self.opt_vector[self.now_id - 1].id)
                                gol.reset_all_value(self.opt_vector)
                                # 获得下一个要读取的操作数
                                self.get_next_opt(self.now_id)
                                flag = False
                                break
                            else:
                                self.last_size = self.last_size + write_bytes
                                break
                        else:
                            temp.append(re_id)
                    temp.reverse()
                    for ii in temp:
                        self.reused_que.append(ii)
                    if (flag) :
                        break
                    # re_id = self.reused_que.pop()
                    # if (not self.check(re_id, self.now_exe_id, self.now_id, self.opt_vector)):
                    #     self.this_opt_buffer_valid = True
                    #     self.this_opt_buffer_index = self.opt_sram_map[self.opt_vector[re_id - 1].name]
                    #
                    #     # 踢出re_id这个操作数
                    #     self.opt_sram_map[self.opt_vector[re_id - 1].name] = 0
                    #     self.buffer_arr[self.this_opt_buffer_index - 1] = 0
                    #
                    #     if (this_opt_need_cycles <= sub_cycles):
                    #         # 完成这个操作数的读取
                    #         sub_cycles -= this_opt_need_cycles
                    #         self.opt_vector[self.now_id - 1].insram = True
                    #         self.opt_sram_map[self.opt_vector[self.now_id - 1].name] = self.this_opt_buffer_index
                    #         self.buffer_arr[self.this_opt_buffer_index -1] = self.now_id
                    #         if (self.opt_vector[self.now_id - 1].reused):
                    #             self.reused_que.appendleft(self.opt_vector[self.now_id - 1].id)
                    #         gol.reset_all_value(self.opt_vector)
                    #         # 获得下一个要读取的操作数
                    #         self.get_next_opt(self.now_id)
                    #     else:
                    #         self.last_size = self.last_size + write_bytes
                    #         break

                    # else:
                    #     self.reused_que.append(re_id)
                    #     break


    # 获得下一个要读取的操作数
    def get_next_opt(self, now_id = 0):
        j = now_id + 1
        if (j > gol.get_len()):
            return
        self.opt_vector = gol.get_all()
        # 找到下一个不在buffer中的操作数
        while (self.opt_vector[j - 1].name in self.opt_sram_map.keys()):
            if (self.opt_sram_map[self.opt_vector[j - 1].name] == 0):
                break
            j += 1
            if (j > len(self.opt_vector)):
                break

        self.now_id = j
        if (self.now_id > gol.get_len()):
            return

        #对这个操作数的一些状态进行定义
        if (self.surplus_buffer_num.qsize()):   #有空闲buffer
            self.this_opt_buffer_index = self.surplus_buffer_num.get()
            self.this_opt_buffer_valid = True
            self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()
            self.last_size = 0
        else:
            self.last_size = 0
            self.this_opt_buffer_valid = False
            self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()
            temp = []
            while(len(self.reused_que)):
                re_id = self.reused_que.pop()
                if (not self.check(re_id, self.now_exe_id, self.now_id, self.opt_vector)):
                    self.last_size = 0
                    self.this_opt_buffer_valid = True
                    self.this_opt_buffer_index = self.opt_sram_map[self.opt_vector[re_id - 1].name]
                    self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()

                    # 踢出re_id这个操作数
                    self.opt_sram_map[self.opt_vector[re_id - 1].name] = 0
                    self.buffer_arr[self.this_opt_buffer_index - 1] = 0
                    break
                else:
                    temp.append(re_id)
            temp.reverse()
            for ii in temp:
                self.reused_que.append(ii)




            # if (len(self.reused_que)):
            #     re_id = self.reused_que.pop()
            #     if (not self.check(re_id, self.now_exe_id, self.now_id, self.opt_vector)):
            #         self.last_size = 0
            #         self.this_opt_buffer_valid = True
            #         self.this_opt_buffer_index = self.opt_sram_map[self.opt_vector[re_id - 1].name]
            #         self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()
            #
            #         #踢出re_id这个操作数
            #         self.opt_sram_map[self.opt_vector[re_id - 1].name] = 0
            #         self.buffer_arr[self.this_opt_buffer_index - 1] = 0
            #
            #     else:
            #         self.reused_que.append(re_id)
            #         self.last_size = 0
            #         self.this_opt_buffer_valid = False
            #         self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()
            # else:
            #     self.last_size = 0
            #     self.this_opt_buffer_valid = False
            #     self.this_opt_size = self.opt_vector[self.now_id - 1].residueL * gol.get_polylen()

        gol.reset_all_value(self.opt_vector)

    #在[start_id, end_id)中找是否有reused_id对应的name的操作数
    def check(self, reused_id, start_id, end_id, opt_vecor):
        re_name = opt_vecor[reused_id - 1].name
        for i in range(start_id, end_id):
            ind_name = opt_vecor[i - 1].name
            if (ind_name == re_name):
                return True
        return False

    #将接下来要执行的操作的操作数写到buffer
    # 出现这种情况，现在dram必然在将这两个操作数写到buffer中，不可能在写更靠前或者靠后的操作数
    def wait_buffer(self, opt1name, opt2name,flag1 = False,flag2 = False, total_cycles = 0):
        if ((not flag1) and (not flag2)):
            if not self.this_opt_buffer_valid:
                print ("wait buffer error!")
                exit(0)
            this_opt_need_cycles = math.ceil((1.0 * self.this_opt_size - self.last_size) / self.dram_bw_1)
            total_cycles += this_opt_need_cycles
            self.complete_one_opt()

            # 获得下一个要读取的操作数
            self.get_next_opt(self.now_id)

            if not self.this_opt_buffer_valid:
                print ("wait buffer error 2!")
                exit(0)
            this_opt_need_cycles = math.ceil((1.0 * self.this_opt_size - self.last_size) / self.dram_bw_1)
            total_cycles += this_opt_need_cycles
            self.last_cycles = total_cycles
            self.complete_one_opt()

            # 获得下一个要读取的操作数
            self.get_next_opt(self.now_id)

        elif (not flag1):
            if not self.this_opt_buffer_valid:
                print ("wait buffer error 3!")
                exit(0)
            this_opt_need_cycles = math.ceil((1.0 * self.this_opt_size - self.last_size) / self.dram_bw_1)
            total_cycles += this_opt_need_cycles
            self.last_cycles = total_cycles
            self.complete_one_opt()

            # 获得下一个要读取的操作数
            self.get_next_opt(self.now_id)
        elif not flag2:
            if not self.this_opt_buffer_valid:
                # print (self.now_exe_id,self.now_id)
                print ("wait buffer error 4!")
                exit(0)
            this_opt_need_cycles = math.ceil((1.0*self.this_opt_size - self.last_size) / self.dram_bw_1)
            total_cycles += this_opt_need_cycles
            self.last_cycles = total_cycles
            self.complete_one_opt()

            # 获得下一个要读取的操作数
            self.get_next_opt(self.now_id)
        return total_cycles

    def wait_buffer_one_opt(self,opt,total_cycles):
        if not self.this_opt_buffer_valid:
            print ("si wait buffer error!")
            exit(0)
        this_opt_need_cycles = math.ceil((1.0 * self.this_opt_size - self.last_size) / self.dram_bw_1)
        total_cycles += this_opt_need_cycles
        self.last_cycles = total_cycles
        self.complete_one_opt()

        # 获得下一个要读取的操作数
        self.get_next_opt(self.now_id)
        return this_opt_need_cycles
    #完成一个操作数从dram到buffer的写
    def complete_one_opt(self):
        self.opt_vector = gol.get_all()
        self.opt_vector[self.now_id - 1].insram = True
        self.opt_sram_map[self.opt_vector[self.now_id - 1].name] = self.this_opt_buffer_index
        self.buffer_arr[self.this_opt_buffer_index - 1] = self.now_id
        if (self.opt_vector[self.now_id - 1].reused):
            self.reused_que.appendleft(self.opt_vector[self.now_id - 1].id)
        gol.reset_all_value(self.opt_vector)

    #获得num个待操作数
    def get_opt(self, num, opt_list = [], opt_iid = []):
        for i in range(num):
            opt = opt_list[i]
            id = opt_iid[i]
            buffer_index = self.opt_sram_map[opt]
            opt_id = self.buffer_arr[buffer_index - 1]
            self.opt_vector = gol.get_all()
            #如果该操作数重用，则保留，否则踢出buffer
            if (not self.opt_vector[id - 1].reused):
                temp = []
                while len(self.reused_que):
                    re_id = self.reused_que.pop()
                    name = self.opt_vector[re_id - 1].name
                    if (name != opt):
                        temp.append(re_id)
                for ii in temp:
                    self.reused_que.appendleft(ii)

                self.opt_sram_map[opt] = 0
                self.buffer_arr[buffer_index - 1] = 0
                self.surplus_buffer_num.put(buffer_index)
            gol.reset_all_value(self.opt_vector)

    #从now_id这个bufffer中获取buffer_bw个操element
    #1,判断是否够取
    #2，够，就直接取走
    #3，不够就先等再取
    def get_data(self):
        cycles = 0
        left_num = self.last_size - self.num
        if(left_num > self.buffer_bw):
            cycles += 1
            self.num += self.buffer_bw
        else:
            need_cycles = math.ceil((self.buffer_bw - left_num) * 1.0 / self.dram_bw_1)
            cycles += need_cycles + 1
            self.num += self.buffer_bw
        return  cycles
