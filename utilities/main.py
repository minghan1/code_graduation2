# -*- coding: utf-8 -*-
import argparse
import param_config_deal as pcd
import os
import simulator as sim
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
    gol.__init(f.opt_vector, f.polylen)

    #调用执行文件
    in_sram_size_bytes = f.Insram_size
    out_sram_size_bytes = f.Outsram_size
    sim = sim.simulator()
    sim.set_param(word_size=1, in_buf_size_bytes=in_sram_size_bytes,\
                  out_buf_size_bytes=out_sram_size_bytes,\
                  input_buf_num=f.buf_num, param_config=f)
    sim.run()

def run(param_default_path,config_default_path):
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

    # 设置跨文件全剧变量opt_vector
    gol.__init(f.opt_vector, f.polylen)

    # 调用执行文件
    in_sram_size_bytes = f.Insram_size
    out_sram_size_bytes = f.Outsram_size
    simm = sim.simulator()
    simm.set_param(word_size=1, in_buf_size_bytes=in_sram_size_bytes, \
                  out_buf_size_bytes=out_sram_size_bytes, \
                  input_buf_num=f.buf_num, param_config=f)
    simm.run()
    return [simm.total_cycles,simm.prefetch_cycles,simm.computer_cycles,simm.write_wait_cycles,simm.write_to_writebuffer_cycles,simm.finish_cycles]