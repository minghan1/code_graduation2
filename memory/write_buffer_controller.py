# -*- coding: utf-8 -*-

import  math
class write_buffer_controller:
    def __init__(self):
        self.write_ptr = 0
        self.read_ptr = 0
        self.write_buffer_size = 0  #以残差后的元素的个数为单位
        self.surplus_size = 0      #剩余可写入大小

        self.buffer_bw = 2048
        self.last_cycles = 0
        self.dram_bw_2 = 0

    def set_params(self, bu_size, dram_bw):
        self.write_buffer_size = bu_size * 1000
        self.surplus_size = bu_size * 1000
        self.dram_bw_2 = dram_bw

    # 更新write_buffer状态，从上一次操作数据都写入buffer,到这一次再次开始写入这段时间
    def update_write_buffer(self, now_cycles):
        sub_cycles = now_cycles - self.last_cycles
        read_max_num = sub_cycles * self.dram_bw_2
        buffer_read_num = self.write_buffer_size - self.surplus_size

        if (read_max_num <= buffer_read_num):
            self.surplus_size += read_max_num
            self.read_ptr = (self.read_ptr + read_max_num) % self.write_buffer_size
        else:
            self.surplus_size += buffer_read_num
            self.read_ptr = (self.read_ptr + buffer_read_num) % self.write_buffer_size

    # 将data_mat写入write_buffer
    def service_memory_requests(self, data_mat_rows, start_cycls):
        #依次写入每一行
        end_cycles = [start_cycls,start_cycls]
        if (self.write_buffer_size < self.buffer_bw):
            print("write buffer error !")
            print ("write buffer is too little !")
            exit(0)
        # #一个
        # while True:
        i = 0
        while(i < data_mat_rows):
            if (self.surplus_size >= self.buffer_bw):
                write_cycles = math.floor(1.0 * self.surplus_size / self.buffer_bw)
                if (write_cycles <= data_mat_rows - i):
                    end_cycles[0] += write_cycles


                    self.surplus_size -= self.buffer_bw * write_cycles
                    self.write_ptr = (self.write_ptr + self.buffer_bw * write_cycles) % self.write_buffer_size
                    # if (self.write_ptr > self.write_buffer_size):
                    #     self.write_ptr -= self.write_buffer_size

                    i += write_cycles
                    # print (write_cycles)
                    buffer_read_num = self.write_buffer_size - self.surplus_size
                    if (buffer_read_num <= self.dram_bw_2 * write_cycles):
                        self.surplus_size += buffer_read_num
                        self.read_ptr = (self.read_ptr + buffer_read_num) % self.write_buffer_size
                    else:
                        self.surplus_size += self.dram_bw_2 * write_cycles
                        self.read_ptr = (self.read_ptr + self.dram_bw_2 * write_cycles) % self.write_buffer_size
                else:
                    write_cycles = data_mat_rows - i
                    end_cycles[0] += write_cycles


                    self.surplus_size -= self.buffer_bw * write_cycles
                    self.write_ptr = (self.write_ptr + self.buffer_bw * write_cycles) % self.write_buffer_size
                    # if (self.write_ptr > self.write_buffer_size):
                    #     self.write_ptr -= self.write_buffer_size

                    i += write_cycles
                    # print (write_cycles)
                    buffer_read_num = self.write_buffer_size - self.surplus_size
                    if (buffer_read_num <= self.dram_bw_2 * write_cycles):
                        self.surplus_size += buffer_read_num
                        self.read_ptr = (self.read_ptr + buffer_read_num) % self.write_buffer_size
                    else:
                        self.surplus_size += self.dram_bw_2 * write_cycles
                        self.read_ptr = (self.read_ptr + self.dram_bw_2 * write_cycles) % self.write_buffer_size
                #########################################
                # 有点慢了!!!!!!!!!
                # buffer_read_num = self.write_buffer_size - self.surplus_size
                #
                # self.surplus_size -= self.buffer_bw
                # self.write_ptr = (self.write_ptr + self.buffer_bw) % self.write_buffer_size
                # end_cycles[0] += 1
                # i += 1
                #
                # if (buffer_read_num <= self.dram_bw_2):
                #     self.surplus_size += buffer_read_num
                #     self.read_ptr = (self.read_ptr + buffer_read_num) % self.write_buffer_size
                # else:
                #     self.surplus_size += self.dram_bw_2
                #     self.read_ptr = (self.read_ptr + self.dram_bw_2) % self.write_buffer_size
            else:
                need_size = self.buffer_bw - self.surplus_size
                need_cycles = math.ceil(need_size * 1.0 / self.dram_bw_2)
                end_cycles[1] += need_cycles
                read_max_num = need_cycles * self.dram_bw_2
                buffer_read_num = self.write_buffer_size - self.surplus_size
                if (read_max_num <= buffer_read_num):
                    self.surplus_size += read_max_num
                    self.read_ptr = (self.read_ptr + read_max_num) % self.write_buffer_size
                else:
                    self.surplus_size += buffer_read_num
                    self.read_ptr = (self.read_ptr + buffer_read_num) % self.write_buffer_size

        self.last_cycles = end_cycles[0] + end_cycles[1] - start_cycls
        end_cycles[0] -= start_cycls
        end_cycles[1] -= start_cycls
        return end_cycles

    #清空输出buffer剩余数据
    def finish(self):
        left_size = self.write_buffer_size - self.surplus_size
        return math.ceil(left_size * 1.0 / self.dram_bw_2)