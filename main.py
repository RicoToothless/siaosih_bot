#!/usr/bin/env pipenv run python

"""
Nonsense plurk bot

Distributed under terms of the WTFPL license.
"""

from poaurk import PlurkAPI
from multiprocessing import Process, Value
import typing
import requests
import json
import re
import loguru
import datetime
import time
import random
import schedule
import sqlite3

class Bot:
    def __init__(self, token_file, database):

        self.main_flag = True
        self.offset = 0
        self.database = database


        self.plurk = PlurkAPI.fromfile(token_file)

        status, user_channel = self.plurk.callAPI("/APP/Realtime/getUserChannel")
        if status:
            self.comet_server_url = user_channel["comet_server"]
            self.comet_server_url = self.comet_server_url.split('?')[0].split('#')[0]
            self.channel_name = user_channel["channel_name"]
            self.offset = 0
            loguru.logger.info(f"Start pulling from comet server: {self.comet_server_url}, channel: {self.channel_name}")
        else:
            loguru.logger.error("Get comet channel failed")
            return

        con = sqlite3.connect(self.database)
        cur = con.cursor()
        cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='users' ''')
        #if the count is 1, then table exists
        if cur.fetchone()[0]==1: 
            loguru.logger.info("Table exists.")
        else:
            #create table
            cur.execute('''CREATE TABLE IF NOT EXISTS users
                         (id real)''')
            loguru.logger.info("Table not exists, create one.")

        con.commit()
        con.close()

    def add_user(self, id):
        if self.if_user(id):
            # If already in
            return False
        con = sqlite3.connect(self.database)
        cur = con.cursor()

        insert_with_param = """INSERT INTO users 
                          (id)
                          VALUES (?);"""

        data_tuple = (id, )
        cur.execute(insert_with_param, data_tuple)

        con.commit()
        con.close()
        return True

    def remove_user(self, id):
        if not self.if_user(id):
            # If not in
            return False
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        cur.execute("DELETE FROM users WHERE id=?;", (id,))

        con.commit()
        con.close()
        return True

    def if_user(self, id):
        result = False
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        cur.execute("SELECT count(id) FROM users WHERE id=?;", (id,))
        if cur.fetchone()[0] >= 1: 
            result = True
        con.close()
        return result

    def is_friend(self, id):
        opt = {
            'user_id': id
        }
        status, resp = self.plurk.callAPI("/APP/Profile/getPublicProfile", options=opt)
        if not status:
            loguru.logger.error(resp)
            return None

        return resp["are_friends"]

    def base36encode(self, number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
        """Converts an integer to a base36 string."""
        if not isinstance(number, int):
            raise TypeError('number must be an integer')

        base36 = ''
        sign = ''

        if number < 0:
            sign = '-'
            number = -number

        if 0 <= number < len(alphabet):
            return sign + alphabet[number]

        while number != 0:
            number, i = divmod(number, len(alphabet))
            base36 = alphabet[i] + base36

        return sign + base36

    def gen_msg(self):
        wara_imgs = [
            "https://i.imgur.com/3G7rJ06.jpg",
            "https://i.imgur.com/641fRAZ.jpg",
            "https://images.plurk.com/4Wr1If26wnRKEZIllQVIzO.jpg",
            "https://images.plurk.com/2OkhSDoYeOsQGdvb5KM9Pn.jpg",
            "https://images.plurk.com/3czlRTuYeTYqCj5vicDQBq.png",
            "https://images.plurk.com/1M3oSnXNOMVxnOose7Wh8v.jpg",
            "https://images.plurk.com/1NiFD84tWntjhd65rqpofb.png",
            "https://images.plurk.com/3A9xyxub8URuxPUkv83Dnr.jpg",
            "https://images.plurk.com/5d1XD5HZ2AwNzrOtnpQt55.jpg",
            "https://images.plurk.com/tvs6tIDqFOlXQz8ctqyVO.png",
            "https://images.plurk.com/sWJm5E69kECFZXaOuOil5.jpg",
            "https://images.plurk.com/2dyrBaeTXMPaFHZIGM38nc.jpg",
            "https://images.plurk.com/2r7SHhlXE6wevIRTkAShDB.jpg",
            "https://images.plurk.com/37E5uFu1po0gijbDhMXNns.jpg",
            "https://images.plurk.com/2Xe3MqVire3OBI86q9NiTm.jpg",
            "https://images.plurk.com/4OdjjlnhEf0Q6Sl16b0Qpe.jpg",
            "https://images.plurk.com/2DsYS1rTQQpEnHYuIGRrlM.jpg",
            "https://images.plurk.com/63h9OSIKfXU0xMdqUcYbug.gif",
            "https://images.plurk.com/5K7Cfwcvf1KLbuDiNLowfX.gif",
            "https://images.plurk.com/4I499E93XC217BKyyrbfxs.jpg",
            "https://images.plurk.com/45aC4lP3VHMtxbJcmCvn7p.gif",
            "https://images.plurk.com/3D6GtdgKVtdXI85rkpv2gF.jpg",
            "https://images.plurk.com/1boeK01koxCaHKp61bNZE7.jpg",
            "https://images.plurk.com/6fyOZT8o4XRFjRsUYhdDPx.jpg",
            "https://images.plurk.com/7bHAJhlYJLKiRtIdE5cAIg.gif",
            "https://images.plurk.com/7qfy5z0gIhssOS0tXPccLb.jpg",
            "https://images.plurk.com/4CvNeGzN8VuSWDa6fdChCA.gif",
            "https://images.plurk.com/6E7j8fqvN4RqGcMP0W8RD4.gif",
            "https://images.plurk.com/6PEEClMbQe34JVhGDrP56A.jpg",
            "https://images.plurk.com/59YJKOGWSSVK0txkTRm5Ns.jpg",
            "https://images.plurk.com/2KirBTzaFncKxmbWpksyHM.jpg",
            "https://images.plurk.com/K19HiFh8FfJ6ikvkGpNkt.jpg",
            "https://images.plurk.com/6ArFHTvOVCho1ACPV1xWUM.jpg",
            "https://images.plurk.com/7vQkaO6QDEsiCi2pdXYNBu.jpg",
            "https://images.plurk.com/4zXWw4Ox7T4Jy1pipddhwF.jpg",
            "https://images.plurk.com/4wE1pgyKoy6q80CAtqYKcV.jpg",
            "https://images.plurk.com/ViZe8EY8Fov7FTWzaD9rG.jpg",
            "https://images.plurk.com/yHMyyfUQmuHzdCR3XefFC.jpg",
            "https://images.plurk.com/46bzj1vbQOjyqtTVsvhKDj.jpg",
            "https://images.plurk.com/7uBif82MSdV9wlwvEKNd0M.jpg",
            "https://images.plurk.com/3aDEp8slhs78INml84qYmR.gif",
            "https://images.plurk.com/2pHGirk3j8vHCTsfJPvjsE.gif",
            "https://images.plurk.com/47LY6qQBbGjTrQDs1fnWvo.jpg",
            "https://images.plurk.com/5VDnGFc25D5WubtOuuGQLs.gif",
            "https://images.plurk.com/1I9bt5RNjdtf8eKuskSdco.gif",
            "https://images.plurk.com/5p0orzgQw0eZBSrrnfVvk8.jpg",
            "https://images.plurk.com/1LBwMqxj15mNDrInv9x09f.jpg",
            "https://images.plurk.com/44ift3DX1eKGITeU1gxzKo.jpg",
            "https://images.plurk.com/1WjLQvgqaEhEptA3GOLtxe.png",
            "https://images.plurk.com/4NI5j9G032Ej94pKz2DVdr.gif",
            "https://images.plurk.com/1fMhrVMAcEheOe8aKYUPMG.jpg",
            "https://images.plurk.com/6i9p8fq1IOPaASKwFlLBEw.jpg",
            "https://images.plurk.com/N9ny55giShpK052P7TU8U.jpg",
            "https://images.plurk.com/1SR9y2XF4N5BJv19sBsh4c.jpg",
            "https://images.plurk.com/274nBeksho0DwJO7Py1dAX.png",
            "https://images.plurk.com/qlzv3DXyXbdc6VcA8Zhpa.gif",
            "https://images.plurk.com/3fIHpkJX0Wfxob2afGzldg.jpg",
            "https://images.plurk.com/6j82CzcV84CNDFr11nk33o.gif",
            "https://images.plurk.com/34UeK1zvIMXufXCcWBZIme.gif",
            "https://images.plurk.com/2yVZq4IqvV4mNkKUNKR3MT.jpg",
            "https://images.plurk.com/6huuRnQ823CP75Zh35GfiN.gif",
            "https://images.plurk.com/QYkMFAmkjnIO5of5xjZRk.jpg",
            "https://images.plurk.com/3mSpHWBu550r2rdKl0wk0c.gif",
            "https://images.plurk.com/5FXj7gQ3SaVhd7xbIG4sP7.gif"
        ]
        rand_num = random.randint(1, 100)

        if rand_num <= 3:
            return '草'
        elif rand_num <= 10:
            return random.choice(wara_imgs) + ' \n笑死'
        elif rand_num <= 20:
            return '哭啊'
        else:
            return '笑死'


    def refresh_channel(self):
        self.plurk.callAPI("/APP/Realtime/getUserChannel")
        self.offset = 0
        loguru.logger.info("Refresh comet channel")


    def comet_main(self, watchdog):
        while self.main_flag:
            q = {
                'channel': self.channel_name,
                'offset':  self.offset
            }

            try:
                resp = requests.get(self.comet_server_url, params=q, timeout=60)
                resp.raise_for_status()
            except requests.exceptions.HTTPError as errh:
                loguru.logger.error(f"Http Error: {errh}")
                continue
            except requests.exceptions.ConnectionError as errc:
                loguru.logger.error(f"Error Connecting: {errc}")
                continue
            except requests.exceptions.Timeout as errt:
                loguru.logger.error(f"Timeout Error: {errt}")
                continue
            except requests.exceptions.RequestException as err:
                loguru.logger.error(f"Request Other Error: {err}")
                continue

            loguru.logger.debug(f"Request url: {resp.url}")
            comet_content = resp.text

            m = re.search(r'CometChannel.scriptCallback\((.*)\);', comet_content)
            try:
                json_content = json.loads(m.group(1))
            except Exception as err:
                loguru.logger.error(f"Json Error: {err}")

            try:
                if "data" in json_content:
                    self.comet_callBack(json_content["data"])
            except Exception as err:
                loguru.logger.error(f"Callback Error: {err}")

            try:
                if "new_offset" in json_content:
                    self.offset = json_content["new_offset"]
                    # loguru.logger.debug(f"Update Offset: {self.offset}")
                    if self.offset<0:
                        loguru.logger.error(f"Offset Error: {offset}")
                        self.refresh_channel()
            except Exception as err:
                loguru.logger.error(f"Offset Error: {err}")

            watchdog.value = 1

    def comet_callBack(self, data):
        for d in data:
            if 'type' not in d:
                loguru.logger.warning(json.dumps(d))
                continue
            if d['type'] == 'new_plurk':
                if not self.is_friend(d["user_id"]):
                    # Not friend, jump
                    continue

                if "不好笑" in d["content"]:
                    res = self.add_user(d["user_id"])
                    if res: loguru.logger.info("Stop user " + str(d["user_id"]))
                elif "好笑嗎" in d["content"]:
                    res = self.remove_user(d["user_id"])
                    if res: loguru.logger.info("Reset user " + str(d["user_id"]))

                if self.if_user(d["user_id"]):
                    continue
                else:
                    opt = {
                        'plurk_id': d['plurk_id'],
                        'qualifier': ':',
                        'content': self.gen_msg()
                    }
                    plurk_id_base36 = self.base36encode(opt['plurk_id'])
                    loguru.logger.info(f"Response to https://www.plurk.com/p/{plurk_id_base36}")
                    self.plurk.callAPI("/APP/Responses/responseAdd", options=opt)


    def routine_main(self, watchdog):
        def add_all_friends():
            self.plurk.callAPI("/APP/Alerts/addAllAsFriends")

        def knock_comet():
            knock_comet_url = "https://www.plurk.com/_comet/generic"
            p = {
                'channel': self.channel_name
            }
            try:
                resp = requests.get(knock_comet_url, params=p, timeout=60)
                resp.raise_for_status()
            except requests.exceptions.HTTPError as errh:
                loguru.logger.error(f"Http Error: {errh}")
                return
            except requests.exceptions.ConnectionError as errc:
                loguru.logger.error(f"Error Connecting: {errc}")
                return
            except requests.exceptions.Timeout as errt:
                loguru.logger.error(f"Timeout Error: {errt}")
                return
            except requests.exceptions.RequestException as err:
                loguru.logger.error(f"Request Other Error: {err}")
                return
            except Exception as err:
                loguru.logger.error(f"Other Error: {err}")
                return

            loguru.logger.debug(f"Request url: {resp.url}")

        def watch_dog():
            if not watchdog.value:
                loguru.logger.error("No response")
                return
            loguru.logger.debug("Running...")
            watchdog.value = 0

        schedule.every(5).seconds.do(add_all_friends)
        schedule.every(1).minutes.do(knock_comet)
        schedule.every(10).minutes.do(watch_dog)
        while self.main_flag:
            try:
                schedule.run_pending()
            except Exception as err:
                loguru.logger.error(f"Schedule Task Error: {err}")
            time.sleep(1)

    def main(self):
        watchdog_flag = Value('i', 1)
        try:
            comet_proc = Process(target=self.comet_main, args=(watchdog_flag,), daemon=True)
            routine_proc = Process(target=self.routine_main, args=(watchdog_flag,), daemon=True)
            comet_proc.start()
            routine_proc.start()
            while True:
                time.sleep(100)
                loguru.logger.debug(f"Running... Comet: {comet_proc.is_alive()}, Routine: {routine_proc.is_alive()}")
        except (KeyboardInterrupt, SystemExit):
            comet_proc.terminate()
            routine_proc.terminate()
            loguru.logger.info("Stop bot.")

if __name__=="__main__":
    loguru.logger.add(
        # f'data/{datetime.date.today():%Y%m%d}.log',
        'data/{time}.log',
        rotation='1 day',
        retention='7 days',
        enqueue=True,
        # level='INFO')
        level='DEBUG')
    bot = Bot("token.txt", "data/users.db")
    bot.main()
