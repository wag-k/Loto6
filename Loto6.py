import collections
import requests
import bs4
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary
import re
import json
import smtplib
from email.mime.text import MIMEText

"""
config.json
{
    "Numbers": [1, 2, 3, 4, 5, 6],
    "MailAddress": "xxx.gmail.com",
    "Password": "password"
}
"""


class Loto6:
    #### Member ####
    """
    soup: bs4.BeautifulSoup
    config: Loto6Config
    """
    def __init__(self):
        pass

    def __init__(self, fpath: str):
        html = self.get_loto6_page(fpath)
        time.sleep(7)
        self.parse_html(html)

    def get_loto6_page(self, url: str) -> str:
        options = Options()
        options.add_argument("--headless")

        driver = webdriver.Chrome(chrome_options=options)
        driver.get(url)
        html = driver.page_source
        return html

    def parse_html(self, html: str) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(html, "html.parser")
        self.soup = soup
        return soup

    def get_main_number(self) -> list:
        t = self.soup.find_all('table')
        main_number = [int(i.text) for i in t[0].find_all('tr')[2].find_all('td')]
        return main_number

    def get_bonus_number(self) -> int:
        t = self.soup.find_all('table') # ちょっともったいないけど
        pat = r"[0-9]+"
        bonus_number = t[0].find_all("tr")[3].find_all("td")[0].text
        bonus_number = re.search(pat, bonus_number).group(0)
        bonus_number = int(bonus_number)
        return bonus_number

    def get_prize(self, rank: int) -> str:
        t = self.soup.find_all('table')
        prize = t[0].find_all("tr")[3+rank].find_all("td")[1].text
        return prize

    # 何等賞か調べて、(等, 本数時, 当選番号, 当選金額)のtupleを返す。
    # はずれの場合は等が-1、当選金額が-1
    def match_numbers(self, selected_numbers: list) -> tuple:
        # 2分探索の方が高速だが、Nが小さいので愚直に調べても不満はない
        rank = -1
        main_numbers = self.get_main_number()
        matched_numbers = []
        prize = "はずれ"

        cnt_match = 0
        unmatched_numbers = []
        for selected_num in selected_numbers:
            if(selected_num in main_numbers):
                cnt_match += 1
                matched_numbers.append(selected_num)
            else:
                unmatched_numbers.append(selected_num)

        bonus_number = self.get_bonus_number()
        rank = self.decide_rank(cnt_match, unmatched_numbers, bonus_number)
        if rank == 2:
            matched_numbers.append(bonus_number)
        
        if 0 < rank:
            prize = self.get_prize(rank)
        
        return (rank, main_numbers, matched_numbers, prize)

    def decide_rank(self, cnt_match: int, unmatched_numbers: list, bonus_number: int) -> int:
        rank = -1
        if cnt_match == 3:
            rank = 5
        elif cnt_match == 4:
            rank = 4
        elif cnt_match == 5:
            if bonus_number in unmatched_numbers:
                rank = 2
            else:
                rank = 3
        elif cnt_match == 6:
            rank = 1
        return rank

class Loto6Config:
    def __init__(self, fpath: str):
        self.load_config(fpath)

    def load_config(self, fpath: str) -> dict:
        with open(fpath) as f:
            config = json.load(f)
        self.config = config
        return config

    def get_numbers(self) -> list:
        return self.config["Numbers"]

    def get_mail_address(self) -> str:
        return self.config["MailAddress"]

    def get_password(self) -> str:
        return self.config["Password"]

def generate_text_loto6_result(res_loto6: tuple, selected_numbers: list)-> str:
    rank = str(res_loto6[0])
    rank = "はずれ" if rank == "-1" else rank + "等"
    title = "Loto6当選状況: " + rank
    message = "当選状況: " + rank + "<BR>"
    main_numbers = res_loto6[1]
    message += "本数字　: " + list_to_str(main_numbers) + "<BR>"
    message += "選択数字: " + list_to_str(selected_numbers) + "<BR>"
    matched_numbers = res_loto6[2]
    message += "当選番号: " + list_to_str(matched_numbers) + "<BR>"
    prize = res_loto6[3]
    message += "　賞金　: " + prize

    return (title, message)
    
def list_to_str(nums: list)->str:
    s = ""
    for num in nums:
        s+= str(num) + ","
    s = s.strip(",")
    return s

def send_mail_with_gmail(to: str, account: str, password: str, title: str, message: str):
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587

    msg = MIMEText(message, "html")     
    msg['Subject'] = title
    msg['From'] = account 
    msg['To'] = to 

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(account, password)
    server.send_message(msg)
    server.quit()

def main():
    # test_loto6()
    # test_config()
    # test_match_numbers()
    run()

def run():
    url = "https://www.mizuhobank.co.jp/takarakuji/loto/loto6/index.html"
    loto6 = Loto6(url)
    config = Loto6Config("./config.json")
    res = loto6.match_numbers(config.get_numbers())
    message = generate_text_loto6_result(res, config.get_numbers())
    send_mail_with_gmail(config.get_mail_address(), config.get_mail_address(), config.get_password(), message[0], message[1])

def test_loto6():
    url = "https://www.mizuhobank.co.jp/takarakuji/loto/loto6/index.html"
    loto6 = Loto6()
    html = loto6.get_loto6_page(url)
    time.sleep(5)
    loto6.parse_html(html)
    main_numbers = loto6.get_main_number()
    bonus_number = loto6.get_bonus_number()
    print(main_numbers)
    print(bonus_number)

def test_config():
    config = Loto6Config("./config.json")
    print(config.get_numbers())
    print(config.get_mail_address())
    print(config.get_password())

def test_match_numbers():
    url = "https://www.mizuhobank.co.jp/takarakuji/loto/loto6/index.html"
    loto6 = Loto6(url)
    config = Loto6Config("./config.json")
    res = loto6.match_numbers(config.get_numbers())
    print(res)
    message = generate_text_loto6_result(res)
    print(message[0])
    print(message[1])
    res = loto6.match_numbers([4, 5, 27, 35, 33, 41])
    print(res)
    message = generate_text_loto6_result(res)
    print(message[0])
    print(message[1])
    res = loto6.match_numbers([1, 2, 3, 4, 5, 6])
    print(res)
    message = generate_text_loto6_result(res)
    print(message[0])
    print(message[1])



if __name__ == "__main__":
    main()