# -*- coding: utf-8 -*-

import math

class stream_creat:
    def __init__(self):
        self.add_lat = 30
        self.mult_lat = 30
        self.ntt_lat = 30

    def set_params(self,add_lat,mult_lat,ntt_lat):
        self.add_lat = add_lat
        self.mult_lat = mult_lat
        self.ntt_lat = ntt_lat
    #返回输入流周期数
    def add_creat(self, size, bw):
        return int(math.ceil(size * 1.0 / bw))

    #返回加操作延迟
    def add_latency(self):
        return self.add_lat

    def mult_creat(self, size, bw):
        return int(math.ceil(size * 1.0 / bw))

    def ntt_creat(self, size, bw):
        return int(math.ceil(size * 1.0 / bw))

    def mult_latency(self):
        return self.mult_lat

    def ntt_latency(self):
        return self.ntt_lat
