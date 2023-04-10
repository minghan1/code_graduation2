# -*- coding: utf-8 -*-

# 简化以下三个地方（对总周期结果影响不大，但是很大减小了实现复杂读）
# 1，不考虑在一个操作执行完成之后更新输入buffer可能遇到的这种情况：
#   下一个要更新的操作的操作数要存储在这个操作的操作数所在buffer，但是在存储的过程中输入的操作数写入的速度比当前操作数读出的快
# 2，在当前操作的目的操作数需要存储到输入buffer中留作重用时，如果输入buffer中没有空闲buffer，则不留这个目的操作数重用，直接输出到输出buffer中去
# 3，输出数据如果需要重用，就同时发送到输入和输出buffer

import argparse
import math

import param_config_deal as pcd
import os
import simulator2 as sim
import gol

# print(os.getcwd())

param_default_path = os.path.join('..','config_file', 'default_file', 'param_config.csv')
config_default_path =  os.path.join('..','config_file', 'default_file', 'opt_config.csv')
result_default_path = os.path.join('..','test_results')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c1', metavar='parameter Config file', type=str,
                        default= '../config_file/default_file/param_config.csv',
                        help='path to the config file 1'
                        )
    parser.add_argument('-c2', metavar='Config file', type=str,
                        default=config_default_path,
                        help='path to the config file 2'
                        )
    parser.add_argument('-p', metavar='log dir', type=str,
                        default=result_default_path,
                        help='path to log dir'
                        )
    args = parser.parse_args()
    config_param = args.c1
    config_opt = args.c2
    logpath = args.p
    # print(config_param, "\n", config_opt, '\n', logpath)
    #获取参数信息
    f = pcd.ParamConfig()
    f.read_param_config_file(config_param)
    f.read_opt_config_file(config_opt)


    #设置跨文件全剧变量opt_vector
    gol.__init(f.opt_vector, f.polylen,len(f.opt_vector_2))

    #调用执行文件
    in_sram_size_bytes = f.Insram_size
    out_sram_size_bytes = f.Outsram_size
    sim = sim.simulator()
    sim.set_param(word_size=1, in_buf_size_bytes=in_sram_size_bytes,\
                  out_buf_size_bytes=out_sram_size_bytes,\
                  input_buf_num=f.buf_num, param_config=f)
    sim.run()

def run(param_default_path,config_default_path,param_custom):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c1', metavar='parameter Config file', type=str,
                        default=param_default_path,
                        help='path to the config file 1'
                        )
    parser.add_argument('-c2', metavar='Config file', type=str,
                        default=config_default_path,
                        help='path to the config file 2'
                        )
    parser.add_argument('-p', metavar='log dir', type=str,
                        default=result_default_path,
                        help='path to log dir'
                        )
    args = parser.parse_args()
    config_param = args.c1
    config_opt = args.c2
    logpath = args.p
    # print(config_param, "\n", config_opt, '\n', logpath)
    # 获取参数信息
    f = pcd.ParamConfig()
    f.read_param_config_file(config_param)
    f.read_opt_config_file(config_opt)

    f.polylen = param_custom.N
    f.dram_bw_1 = param_custom.dram_bw_1
    f.dram_bw_2 = param_custom.dram_bw_2
    f.computer_latency = param_custom.computer_latency
    f.buf_num = param_custom.buffer_num
    f.prefetch_buf_num = param_custom.prefetch_num
    f.Outsram_size = param_custom.out_buffer_size

    # 设置跨文件全剧变量opt_vector
    gol.__init(f.opt_vector, f.polylen,f.optlen)
    # 调用执行文件
    in_sram_size_bytes = f.Insram_size
    out_sram_size_bytes = f.Outsram_size
    simm = sim.simulator()
    simm.set_param(word_size=1, in_buf_size_bytes=in_sram_size_bytes, \
                  out_buf_size_bytes=out_sram_size_bytes, \
                  input_buf_num=f.buf_num, param_config=f)
    simm.run()
    minimum_cycles = math.ceil(f.polylen * 60 * f.optlen * 1.0 / f.dram_bw_2)  + simm.prefetch_cycles
    # print simm.total_cycles - minimum_cycles
    # print (simm.total_cycles,simm.minimum_cycles+simm.prefetch_cycles+simm.computer_cycles+simm.read_stall_cycles+simm.write_to_writebuffer_cycles+simm.finish_cycles)
    return [simm.total_cycles,simm.minimum_cycles,simm.prefetch_cycles,simm.computer_cycles,simm.read_stall_cycles,simm.write_to_writebuffer_cycles,simm.finish_cycles]