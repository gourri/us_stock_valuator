# -*- coding: utf-8 -*-
import os
import pandas as pd
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import csv
from datetime import datetime
import time
import sys

from multiprocessing import Process

import url_handler
import data_collector
import valuator

now = datetime.now()
expected_income_ratio = 8.12

stock_code_file = "./ual.csv"     # Test data

columnlist = ['code', 'name', 'price', 'EV/CF', 'EPS', 'PBR', 'dividend', 'ROE%', 'ROA(8)%', 'ROIC(8)%', 'FCFA(8)%', 'P_MM', 'EBIT/EV', 'GPA', 'ROIC%', 'S-RIM\nprice', 'S-RIM\nmargin', 'Templeton\nprice', 'Templeton\nrank', 'P_FS', 'STA', 'SNOA', 'Moat']


def us_run(us_codes, proc_num, list_chunk = 300, login_id="", login_passwd="", result_file_header = "./result_data/us_choosen_"):
    print ("proc_num = {}".format(proc_num))
    try:
        os.makedirs("./itooza/us/"+now.strftime("%Y%m%d")+"/")    
        print("Directory ", "./itooza/us/"+now.strftime("%Y%m%d")+"/",  " Created ")
    except FileExistsError:
        print("Directory ", "./itooza/us/"+now.strftime("%Y%m%d")+"/",  " Already exists")

    stock_code_name_dict = {}
    s_rim_buy = []
    templeton_buy = []
    alldfcontents = []
    dfcontents = []
    all_revisit_contents = []
    revisit_contents = []

    for us_code in us_codes:
        try:
            stock_code = us_code[0]
            stock_code_name_dict[us_code[0]] = us_code[1]
            print("\n\n\nus_code = {}, stock_name = {}".format(stock_code, us_code[1]))
            s_rim_price = 0
            templeton_price = 0
            
            df_investing, df_financial, current_price, ev = data_collector.read_data_from_itooza_us(stock_code, login_id, login_passwd)
            print(df_investing)
            print(df_financial)
            
            ev_cf_ratio = valuator.calculate_ev_cf_ratio(ev, df_financial)
            print ("EV/CashFlow = {}".format(ev_cf_ratio))

            sta, snoa = valuator.calculate_sta_snoa_probm_us(df_financial)
            
            stock_name_to_print = "{}, {}".format(stock_code, stock_code_name_dict[stock_code])

            # Get S-RIM Price
            s_rim_price = valuator.s_rim_calculator_us(df_investing, expected_income_ratio, current_price)
            if s_rim_price > current_price:
                print ("S-RIM: BUY {}".format(stock_name_to_print))
                s_rim_buy.append((stock_code, int(s_rim_price)))
            else:
                print ("S-RIM: DON'T BUY {}".format(stock_name_to_print))

            # Get Templeton Price
            templeton_price = valuator.templeton_price_calculator_us(df_investing)
            if templeton_price > current_price:
                print ("Templeton: Strong BUY {}".format(stock_name_to_print))
                templeton_buy.append((stock_code, int(templeton_price)))
            elif (templeton_price * 2) > current_price:
                print ("Templeton: Consider BUY {}".format(stock_name_to_print))
                templeton_buy.append((stock_code, int(templeton_price)))
            else:
                print ("Templeton: DON'T BUY {}".format(stock_name_to_print))

            fs_score = valuator.calculate_fs_score_us(df_investing, df_financial)
            if fs_score >= 7:
                print ("FS score: GOOD {}".format(stock_name_to_print))

            p_fs = fs_score/10

            moat = valuator.is_economic_moat_us(df_investing, df_financial)
            ebit_ev = valuator.get_ebit_ev_us(df_financial, ev)
            gpa = valuator.get_gpa_us(df_financial)
            roic = float(df_investing.loc[20][1].replace('%',''))

            roa_8, roic_8, fcfa_8, p_mm = valuator.calc_economic_moat_us(df_investing, df_financial)
            
            # Save data
            df_investing.to_csv("./itooza/us/"+now.strftime("%Y%m%d")+"/"+stock_code+"_investing.csv", mode="w")
            df_financial.to_csv("./itooza/us/"+now.strftime("%Y%m%d")+"/"+stock_code+"_financial.csv", mode="w")

            dfcontents.append(stock_code)
            dfcontents.append(stock_code_name_dict[stock_code])
            dfcontents.append("{:.2f}".format(current_price))
            dfcontents.append("{:.2f}".format(ev_cf_ratio))     # EV/CashFlow
            dfcontents.append(df_investing.loc[1][1])     # EPS Consolidated
            dfcontents.append(df_investing.loc[8][1])     # PBR
            dfcontents.append(df_investing.loc[3][1])     # dividend
            dfcontents.append(df_investing.loc[18][1])     # ROE
            dfcontents.append("{:.2f}".format(roa_8*100))     # ROA(8)
            dfcontents.append("{:.2f}".format(roic_8*100))     # ROIC(8)
            dfcontents.append("{:.2f}".format(fcfa_8*100))     # FCFA(8)
            dfcontents.append(p_mm)     # MM
            dfcontents.append(ebit_ev)     # EBIT/EV
            dfcontents.append(gpa)     # GPA
            dfcontents.append(roic)     # ROIC
            dfcontents.append("{:.2f}".format(s_rim_price))
            dfcontents.append("{:.2f}".format(((s_rim_price-current_price)/current_price)*100)+"%")
            dfcontents.append("{:.2f}".format(templeton_price))
            if (templeton_price > current_price):
                dfcontents.append(1)
            elif ((templeton_price *2) > current_price):
                dfcontents.append(2)
            else:
                dfcontents.append(99)
            dfcontents.append(p_fs)
            dfcontents.append('{:.2f}%'.format(sta))
            dfcontents.append('{:.2f}%'.format(snoa))
            dfcontents.append(moat)

            if len(dfcontents) > 0:
                alldfcontents.append(dfcontents)
                dfcontents = []
        except Exception as e:
            if e == KeyboardInterrupt:
                break
            else:
                revisit_contents.append(stock_code)
                revisit_contents.append(stock_code_name_dict[stock_code])
                revisit_contents.append(str(e))
                all_revisit_contents.append(revisit_contents)
                revisit_contents = []
                continue

    result_df = pd.DataFrame(columns=columnlist, data=alldfcontents)

    print(result_df)
    result_file = result_file_header
    result_file = result_file + now.strftime("%Y%m%d") + "_" + str(proc_num) + ".csv"
    print ("result_file = {}".format(result_file))
    result_df.to_csv(result_file, mode="w")

    if len(all_revisit_contents) > 0 and len(all_revisit_contents[0]) > 3:
        revisit_columns = ['code', 'name', 'reason']
        revisit_df = pd.DataFrame(columns=revisit_columns, data=all_revisit_contents)
        revisit_df.to_csv('revisit_list_'+now.strftime("%Y%m%d") + "_" + str(proc_num) +'.csv', mode="w")


def us_run_from_files(us_codes, proc_num, data_location = "./itooza/us/20200207/", result_file_header = "./result_data/us_choosen_"):
    print ("proc_num = {}".format(proc_num))

    stock_code_name_dict = {}
    s_rim_buy = []
    templeton_buy = []
    alldfcontents = []
    dfcontents = []
    all_revisit_contents = []
    revisit_contents = []

    for us_code in us_codes:
        try:
            stock_code = us_code[0]
            s_rim_price = 0
            templeton_price = 0
            
            df_investing, df_financial, current_price, ev = data_collector.read_data_from_files_us(stock_code, data_location.split('/')[-2])
            print(df_investing)
            print(df_financial)

            ev_cf_ratio = valuator.calculate_ev_cf_ratio(ev, df_financial)
            print ("EV/CashFlow = {}".format(ev_cf_ratio))
            sta, snoa = valuator.calculate_sta_snoa_probm_us(df_financial)

            # Get S-RIM Price
            s_rim_price = valuator.s_rim_calculator_us(df_investing, expected_income_ratio, current_price)
            if s_rim_price > current_price:
                print ("S-RIM: BUY {}".format(stock_code))
                s_rim_buy.append((stock_code, int(s_rim_price)))
            else:
                print ("S-RIM: DON'T BUY {}".format(stock_code))

            # Get Templeton Price
            templeton_price = valuator.templeton_price_calculator_us(df_investing)
            if templeton_price > current_price:
                print ("Templeton: Strong BUY {}".format(stock_code))
                templeton_buy.append((stock_code, int(templeton_price)))
            elif (templeton_price * 2) > current_price:
                print ("Templeton: Consider BUY {}".format(stock_code))
                templeton_buy.append((stock_code, int(templeton_price)))
            else:
                print ("Templeton: DON'T BUY {}".format(stock_code))

            fs_score = valuator.calculate_fs_score_us(df_investing, df_financial)
            if fs_score >= 7:
                print ("FS score: GOOD {}".format(stock_code))

            p_fs = fs_score/10

            moat = valuator.is_economic_moat_us(df_investing, df_financial)
            ebit_ev = valuator.get_ebit_ev_us(df_financial, ev)
            gpa = valuator.get_gpa_us(df_financial)
            roic = float(df_investing.loc[20][1].replace('%',''))

            roa_8, roic_8, fcfa_8, p_mm = valuator.calc_economic_moat_us(df_investing, df_financial)
            
            # Save data
            df_investing.to_csv("./itooza/us/"+now.strftime("%Y%m%d")+"/"+stock_code+"_investing.csv", mode="w")
            df_financial.to_csv("./itooza/us/"+now.strftime("%Y%m%d")+"/"+stock_code+"_financial.csv", mode="w")

            dfcontents.append(stock_code)
            dfcontents.append("{:.2f}".format(current_price))
            dfcontents.append("{:.2f}".format(ev_cf_ratio))     # EV/CashFlow
            dfcontents.append(df_investing.loc[1][1])     # EPS Consolidated
            dfcontents.append(df_investing.loc[8][1])     # PBR
            dfcontents.append(df_investing.loc[3][1])     # dividend
            dfcontents.append(df_investing.loc[18][1])     # ROE
            dfcontents.append("{:.2f}".format(roa_8*100))     # ROA(8)
            dfcontents.append("{:.2f}".format(roic_8*100))     # ROIC(8)
            dfcontents.append("{:.2f}".format(fcfa_8*100))     # FCFA(8)
            dfcontents.append(p_mm)     # MM
            dfcontents.append(ebit_ev)     # EBIT/EV
            dfcontents.append(gpa)     # GPA
            dfcontents.append(roic)     # ROIC
            dfcontents.append("{:.2f}".format(s_rim_price))
            dfcontents.append("{:.2f}".format(((s_rim_price-current_price)/current_price)*100)+"%")
            dfcontents.append("{:.2f}".format(templeton_price))
            if (templeton_price > current_price):
                dfcontents.append(1)
            elif ((templeton_price *2) > current_price):
                dfcontents.append(2)
            else:
                dfcontents.append(99)
            dfcontents.append(p_fs)
            dfcontents.append('{:.2f}%'.format(sta))
            dfcontents.append('{:.2f}%'.format(snoa))
            dfcontents.append(moat)

            if len(dfcontents) > 0:
                alldfcontents.append(dfcontents)
                dfcontents = []
        except Exception as e:
            if e == KeyboardInterrupt:
                break
            else:
                revisit_contents.append(stock_code)
                revisit_contents.append(str(e))
                all_revisit_contents.append(revisit_contents)
                revisit_contents = []
                continue

    result_df = pd.DataFrame(columns=columnlist, data=alldfcontents)

    print(result_df)
    result_file = result_file_header
    result_file = result_file + now.strftime("%Y%m%d") + "_" + str(proc_num) + ".csv"
    print ("result_file = {}".format(result_file))
    result_df.to_csv(result_file, mode="w")

    if len(all_revisit_contents) > 3:
        revisit_columns = ['code', 'reason']
        revisit_df = pd.DataFrame(columns=revisit_columns, data=all_revisit_contents)
        revisit_df.to_csv('revisit_list_'+now.strftime("%Y%m%d") + "_" + str(proc_num) +'.csv', mode="w")


def concat_dataframes(result_file_name, cnt, result_file_header  = "./result_data/us_choosen_"):
    dfs = []
    for proc_num in range(0, cnt):
        result_file = result_file_header + now.strftime("%Y%m%d") + "_" + str(proc_num) + ".csv"
        print("result_file = {}".format(result_file))
        try:
            df = pd.read_csv(result_file)
            dfs.append(df)
        except Exception as e:
            print("File not opened {} with exception ({}).".format(result_file, e))
            continue
    result_df = pd.concat(dfs)

    result_df['EBIT/EV rank'] = result_df['EBIT/EV'].rank(ascending=0)
    result_df['GPA rank'] = result_df['GPA'].rank(ascending=0)
    result_df['P_FP'] = (result_df['ROA(8)%'] + result_df['ROIC(8)%'] + result_df['FCFA(8)%'] + result_df['P_MM'])/4
    result_df['P_FS rank'] = result_df['P_FS'].rank(ascending=0)
    result_df['P_FP rank'] = result_df['P_FP'].rank(ascending=0)
    result_df['QV'] = 0.5*result_df['P_FP'] + 0.5*result_df['P_FS']
    result_df['QV rank'] = 0.5*result_df['P_FP rank'] + 0.5*result_df['P_FS rank']

    result_df.drop(result_df.columns[[0]], axis=1, inplace=True)

    result_df.to_csv(result_file_name)


def send_email(result_file_name):
    # Send email based on naver email
    sendEmail = ""  # Need to sender's naver email address
    recvEmail = ""  # Need to receiver email address
    password = ""  # Need to naver password

    smtpName = "smtp.naver.com" #smtp server address
    smtpPort = 587 #smtp port
    
    msg = MIMEMultipart()
    msg['Subject'] ="[{}] Valuation Result for US Stock Market".format(now.strftime("%Y-%m-%d"))
    msg['From'] = sendEmail
    msg['To'] = recvEmail

    text = "[{}] The calculated result is attached as {}.".format(now.strftime("%Y-%m-%d"), result_file_name)
    msg.attach(MIMEText(text))

    with open(result_file_name, "rb") as fil:
        part = MIMEApplication(fil.read(),Name=result_file_name)
    # After the file is closed
    part['Content-Disposition'] = 'attachment; filename="%s"' % result_file_name.split('/')[-1]
    msg.attach(part)

    print(msg.as_string())

    s=smtplib.SMTP(smtpName, smtpPort)   # connect mail server
    s.starttls()    # TLS security
    s.login("", password)    # login
    s.sendmail(sendEmail, recvEmail, msg.as_string())     # send mail with converting to string
    s.close()       # close smtp connection


if __name__ == "__main__":
    procs = []
    process_cnt = 1
    stock_cnt = 6714

    login_id = ""
    login_passwd = ""
    try:
        os.makedirs("./result_data/")    
        print("Directory ", "./result_data/",  " Created ")
    except FileExistsError:
        print("Directory ", "./result_data/",  " Already exists")

    result_file_header = "./result_data/us_choosen_"
    
    chunk = int(stock_cnt/process_cnt)

    print ("len(argv) = {}".format(len(sys.argv)))
    for t in sys.argv:
        print ("argv = {}".format(t))

    if (len(sys.argv) >= 2):
        stock_code_file = sys.argv[1]
    if (len(sys.argv) >= 3):
        login_id = sys.argv[2]
    if (len(sys.argv) >= 4):
        login_passwd = sys.argv[3]

    f = open(stock_code_file, 'r')
    tmp_us_codes = list(csv.reader(f))
    print(len(tmp_us_codes))
    print(tmp_us_codes)
    us_codes = [tmp_us_codes[i * chunk:(i + 1) * chunk] for i in range((len(tmp_us_codes) + chunk - 1) // chunk )]
    print(len(us_codes))

    print("chunk = {}".format(chunk))
    time.sleep(5)

    for index in range(0, process_cnt):
        proc = Process(target=us_run ,args=(us_codes[index], index, chunk, login_id, login_passwd))
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()
    
    concat_dataframes(result_file_header + now.strftime("%Y%m%d") + ".csv", process_cnt, "./result_data/us_choosen_")
    #send_email(result_file_header + now.strftime("%Y%m%d") + ".csv")