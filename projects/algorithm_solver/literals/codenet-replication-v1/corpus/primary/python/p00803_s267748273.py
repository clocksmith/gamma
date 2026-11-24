#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Problems 1224
2001年 アジア地区予選 函館大会 問題A Starship Hakodate-maru
"""
while True:
    balls = int(input())
    ans = 0
    if balls == 0: # ボールの数が0個なら終了する
        break
    for cs in range(54):
        for ts in range(96):
            if pow(cs,3) <= balls:
                ans = max(ans, pow(cs,3))
            if ts*(ts+1)*(ts+2)//6 <= balls:
                ans = max(ans, ts*(ts+1)*(ts+2)//6)
            if pow(cs,3) + ts*(ts+1)*(ts+2)//6 <= balls:
                ans = max(ans, pow(cs,3) + ts*(ts+1)*(ts+2)//6)
    print(ans)
