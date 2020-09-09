# -*- coding: utf-8 -*-
import sys
import datetime
import sys
import re
import pandas as pd
import statistics

def s_rim_calculator_us(df, expected_income_ratio, current_price):
    print("current_price = {}".format(current_price))
    try:
        #print (df.loc[0])
        bps = float(df.loc[2][1])      # Book-value Per Share
        weighted_sum = 0.0
        total_weight = 0.0
        for idx, weight in enumerate(df.loc[0]):
            if idx != 0:
                print ("weight = {}, ROE(%) = {}".format(weight, df.loc[18][idx]))
                if df.loc[18][idx] != '':
                    if df.loc[18][idx] != 'N/A':
                        weighted_sum = weighted_sum + (float(weight) * float(df.loc[18][idx].replace('%','').replace(',','')))
                        total_weight = total_weight + float(weight)
        weighted_avg = weighted_sum / total_weight
        s_rim_price = bps * (weighted_avg / expected_income_ratio)

        print (s_rim_price)
        return s_rim_price
    except Exception as e:
        print ("Can't calculate S-RIM price due to exception({})".format(e))
        return 0
        #raise e


def templeton_price_calculator_us(df):
    try:
        eps_sum = 0
        latest_eps = float(df.loc[1][1])
        eps_five_period_ago = float(df.loc[1][6])
        growth_rate = (latest_eps - eps_five_period_ago) / abs(eps_five_period_ago)

        eps_sum = eps_sum + (growth_rate * latest_eps) + latest_eps
        eps_year_list = [eps_sum]
        for i in range(1, 5):
            new_eps = eps_year_list[i-1] * growth_rate + eps_year_list[i-1]
            eps_year_list.append(new_eps)
            eps_sum = eps_sum + new_eps
        print ("eps_sum = {}, eps_year_list = {}".format(eps_sum, eps_year_list))
        return eps_sum
    except Exception as e:
        print ("Can't calculate Templeton price due to exception({})".format(e))
        return 0
        #raise e


def calculate_sta_snoa_probm_us(df_financial):
    # STA = (net_income - operating_cash_flow) / total_asset
    # SNOA = (operating_asset - operating_liability) / total_asset
    # more STA/SNOA more risky (0-100%)

    # Very hard to get PROBM
    # PROBM = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI
    # PMAN = CDF(PROBM)
    # PMAN = 0 -> safe, PMAN = 1 -> risky

    total_asset = float(df_financial.loc[26][1].replace(',',''))
    net_income = float(df_financial.loc[13][1].replace(',',''))
    operating_cash_flow = float(df_financial.loc[39][1].replace(',',''))
    operating_asset = float(df_financial.loc[27][1].replace(',',''))
    operating_liability = float(df_financial.loc[36][1].replace(',',''))

    sta = (net_income - operating_cash_flow) / total_asset
    snoa = (operating_asset - operating_liability) / total_asset

    return sta * 100, snoa * 100


def calculate_fs_score_us(df_investing, df_financial):
    # ROA > 0 --> 1
    # FCFA = (free_cash_flow/total_asset) > 0 --> 1
    # accural = FCFA > ROA --> 1
    # lever_delta = delta(long_liability / total_asset) > 0 --> 1
    # liquid_delta = delta(current_asset - current_liability) > 0 --> 1
    # NEqIss = (buying_stock - stock_increase) > 0
    # ROA_delta > 0 --> 1
    # FCFA_delta > 0 --> 1
    # margin_delta = delta(growth_margin/sales) > 0 --> 1
    # turn_delta = delta(total_asset_turnover_ratio)

    #print ('len(df_financial.index) = {}'.format(len(df_financial.index)))
    try:
        delta_periods = 4
        if len(df_financial.columns) == 10:
            delta_periods = 1
        #print("df_financial.columns")

        index_total_asset = 24
        index_fcf = 39
        index_liability = 31
        if len(df_financial.index) != 40:
            #print("len(df_financial.index)")
            index_total_asset = 26
            index_fcf = 45
            index_liability = 37
        #print("total_asset = {}".format(df_financial.loc[26][1]))
        total_asset = float(df_financial.loc[index_total_asset][1].replace(',',''))
        #print("total_asset")
        pre_total_asset = float(df_financial.loc[index_total_asset][1+delta_periods].replace(',',''))
        #print("pre_total_asset")
        ROA = 1 if (float(df_investing.loc[19][1].replace('%','')) / 100) > 0 else 0
        #print("ROA")
        FCFA = 1 if (float(df_financial.loc[index_fcf][1].replace(',',''))/total_asset) > 0 else 0
        #print("FCFA")
        roa = float(df_investing.loc[19][1].replace('%','')) / 100
        #print("roa")
        fcfa = float(df_financial.loc[index_fcf][1].replace(',',''))/total_asset
        #print("fcfa")
        pre_fcfa = float(df_financial.loc[index_fcf][1+delta_periods].replace(',',''))/total_asset
        #print("pre_fcfa")
        accural = 1 if fcfa > roa else 0
        #print("accural")
        curr_lever = float(df_financial.loc[index_liability][1].replace(',',''))/total_asset
        #print("curr_lever")
        pre_lever = float(df_financial.loc[index_liability][1+delta_periods].replace(',',''))/pre_total_asset
        #print("pre_lever")
        lever_delta = 1 if (curr_lever - pre_lever) > 0 else 0
        #print("lever_delta")
        curr_liquid = float(df_financial.loc[index_total_asset][1].replace(',','')) - float(df_financial.loc[index_liability][1].replace(',',''))
        #print("curr_liquid")
        pre_liquid = float(df_financial.loc[index_total_asset][1+delta_periods].replace(',','')) - float(df_financial.loc[index_liability][1+delta_periods].replace(',',''))
        #print("pre_liquid")
        liquid_delta = 1 if (curr_liquid - pre_liquid) > 0 else 0
        #print("liquid_delta")
        NEqIss = 1  # how to get information
        ROA_delta = 1 if (float(df_investing.loc[19][1].replace('%','')) - float(df_investing.loc[19][1+delta_periods].replace('%',''))) > 0 else 0
        #print("ROA_delta")
        FCFA_delta = 1 if (fcfa - pre_fcfa) > 0 else 0
        #print("FCFA_delta")
        curr_margin = float(df_financial.loc[2][1].replace(',','')) / float(df_financial.loc[0][1].replace(',',''))
        #print("curr_margin")
        pre_margin = float(df_financial.loc[2][1+delta_periods].replace(',','')) / float(df_financial.loc[0][1+delta_periods].replace(',',''))
        #print("pre_margin")
        margin_delta = 1 if (curr_margin - pre_margin) > 0 else 0
        #print("margin_delta")
        turn_delta = 1 if (float(df_investing.loc[index_total_asset][1].replace('%','')) - float(df_investing.loc[index_total_asset][1+delta_periods].replace('%',''))) > 0 else 0
        #print("turn_delta")

        # good: 7,8,9,10
        fs_score = int(ROA+FCFA+accural+lever_delta+liquid_delta+NEqIss+ROA_delta+FCFA_delta+margin_delta+turn_delta)
    except Exception as e:
        print ("Can't calculate FS score: {}".format(e))
        fs_score = 0
        return 0
        #raise e

    return fs_score


def is_economic_moat_us(df_investing, df_financial):
    '''
    1. 투하자본수익률(ROIC)
    2. 매출액 증가율
    3. 주당순이익(EPS) 증가율
    4. 주당순자산(BPS) 증가율
    5. 잉여현금흐름 증가율
    '''
    delta_periods = 4
    if len(df_financial.columns) == 10:
        delta_periods = 1
    print("Calculating Economic Moats..")

    try:
        roic = float(df_investing.loc[20][1].replace('%',''))
        print("ROIC = {}".format(roic))

        curr_sales = float(df_financial.loc[0][1].replace(',',''))
        pre_sales = float(df_financial.loc[0][1+delta_periods].replace(',',''))
        sales_increase = (curr_sales - pre_sales) / pre_sales
        print("Sales increase = {}".format(sales_increase))

        curr_eps = float(df_investing.loc[1][1])
        pre_eps = float(df_investing.loc[1][1+delta_periods])
        eps_increase = (curr_eps - pre_eps) / pre_eps
        print("EPS increase = {}".format(eps_increase))

        curr_bps = float(df_investing.loc[2][1])
        pre_bps = float(df_investing.loc[2][1+delta_periods])
        bps_increase = (curr_bps - pre_bps) / pre_bps
        print("BPS increase = {}".format(bps_increase))

        curr_cf = float(df_investing.loc[17][1].replace('%',''))
        pre_cf = float(df_investing.loc[17][1+delta_periods].replace('%',''))
        cf_increase = (curr_cf - pre_cf) / pre_cf
        print("Cash Flow increase = {}".format(cf_increase))

        moat_cnt = 0
        if roic >= 10:
            moat_cnt = moat_cnt +1
        if sales_increase >= 0.1:
            moat_cnt = moat_cnt +1
        if eps_increase >= 0.1:
            moat_cnt = moat_cnt +1
        if bps_increase >= 0.1:
            moat_cnt = moat_cnt +1
        if cf_increase >= 10:
            moat_cnt = moat_cnt +1

        return moat_cnt

    except Exception as e:
        print ("Can't calculate economic moat: {}".format(e))
        return 0
        #raise e


def calc_economic_moat_us(df_investing, df_financial):
    '''
    (1) 경제적 해자
    ROA(8) = 8년 기하평균 총자산이익률
        - ROA = 당기순이익(t)/총자산(t)
        - P_ROA(8) = 투자 유니버스 전체 ROA(8)에서 차지하는 비율
    ROIC(8) = 8년 기하평균 투하자본이익률
        - ROIC = EBIT(t)/IC(t)
        - P_ROIC(8) = 투자 유니버스 전체 ROIC(8)에서 차지하는 비율
    장기 FCFA = 총자산 대비 장기 잉여현금흐름
        - 8년 잉여현금흐름의 총합/총자산
        - P_FCFA = 투자 유니버스 전체 장기 FCFA에서 차지하는 비율
    MG = Margin Growth = 매출총이익률 성장률
        - 매출총이익률 성장률의 8년 기하평균
        - P_MG = 투자 유니버스 전체 MG에서 차지하는 비율
    MS = Margin Stability = 매출총이익률 안정성
        - 매출총이익률의 8년 평균(%)/매출총이익률의 8년 표준편차(%)
        - P_MS = 투자 유니버스 전체 MS에서 차지하는 비율
    MM = Margin Max = 최대 마진
        - Max[P_MG, P_MS] = P_MG와 P_MS 중 최댓값
    경제적 해자 점수(P_FP)
        - 투자 유니버스 전체의 AVG[P_ROA(8), P_ROIC(8), P_FCFA, MM]에서 차지하는 비율
        - AVG[P_ROA(8), P_ROIC(8), P_FCFA, MM]은 4개 변수의 평균
    '''
    print("Calculating Economic Moats..")
    roa_8 = 0
    roic_8 = 0
    fcfa_8 = 0
    cnt_roa_8 = 0
    cnt_roic_8 = 0
    cnt_fcfa_8 = 0
    t_margin_8 = []
    mg_8 = 0
    ms_8 = 0
    try:
        delta_periods = 4
        if len(df_financial.columns) == 10:
            delta_periods = 1

        index_total_asset = 24
        index_fcf = 39
        if len(df_financial.index) != 40:
            index_total_asset = 26
            index_fcf = 45

        for i in range(1, (delta_periods * 8 + 1), delta_periods):
            if df_investing.loc[19][i] != 'N/A':
                roa_8 = roa_8 + float(df_investing.loc[19][i].replace('%',''))/100
                cnt_roa_8 = cnt_roa_8 + 1
                print("roa_8 = {}".format(roa_8))
            if df_investing.loc[20][i] != 'N/A':
                roic_8 = roic_8 + float(df_investing.loc[20][i].replace('%',''))/100
                cnt_roic_8 = cnt_roic_8 + 1
                print("roic_8 = {}".format(roic_8))
            if df_financial.loc[index_fcf][i] != 'N/A' and df_financial.loc[index_total_asset][i] != 'N/A':
                fcfa_8 = fcfa_8 + float(df_financial.loc[index_fcf][i].replace(',','')) / float(df_financial.loc[index_total_asset][i].replace(',',''))
                cnt_fcfa_8 = cnt_fcfa_8 + 1
                print("fcfa_8 = {}".format(fcfa_8))
            if df_investing.loc[13][i] != 'N/A':
                t_margin_8.append(float(df_investing.loc[13][i].replace('%','')))
                print("t_margin_8 = {}".format(t_margin_8))
        roa_8 = roa_8 / cnt_roa_8
        roic_8 = roic_8 / cnt_roic_8
        fcfa_8 = fcfa_8 / cnt_fcfa_8
        mg_8 = statistics.geometric_mean(t_margin_8) # with python3.8
        if statistics.stdev(t_margin_8) != 0:
            ms_8 = statistics.mean(t_margin_8)/statistics.stdev(t_margin_8)
        else:
            ms_8 = 0
        print ("roa_8={}, roic_8={}, fcfa_8={}, mg_8={}, ms_8={}".format(roa_8, roic_8, fcfa_8, mg_8, ms_8))
        return roa_8, roic_8, fcfa_8, max(mg_8, ms_8)
    except Exception as e:
        print ("Can't calculate economic moat:{}".format(e))
        return roa_8, roic_8, fcfa_8, max(mg_8, ms_8)
        #raise e

def get_ebit_ev_us(df_financial, ev):
    ebit = float(df_financial.loc[7][1].replace(',','')) + float(df_financial.loc[10][1].replace(',',''))
    if ev != 0:
        return ebit/ev
    else:
        return 0

def calculate_ev_cf_ratio(ev, df_financial):
    print("Calculating EV/CashFlow..")
    try:
        delta_periods = 4
        if len(df_financial.columns) == 10:
            delta_periods = 1

        index_ocf = 33
        if len(df_financial.index) != 40:
            index_ocf = 39
        ocf_8 = 0
        cnt = 0
        for i in range(1, (delta_periods * 8 + 1), delta_periods):
            if df_financial.loc[index_ocf][i] != 'N/A':
                ocf_8 = ocf_8 + float(df_financial.loc[index_ocf][i].replace(',',''))
                cnt = cnt + 1
                print("ocf_8 = {}".format(ocf_8))
        ocf_avg = ocf_8 / cnt
        print ("EV, OCF = {}, {}".format(ev, ocf_avg))
        return float(ev)/ocf_avg
    except Exception as e:
        print ("Can't calculate EV/CashFlow {}".format(e))
        return 0

def get_gpa_us(df_financial):
    index_total_asset = 24
    if len(df_financial.index) != 40:
        index_total_asset = 26
    total_asset = float(df_financial.loc[index_total_asset][1].replace(',',''))
    if total_asset > 0:
        return float(df_financial.loc[2][1].replace(',','')) / total_asset
    else:
        return 0