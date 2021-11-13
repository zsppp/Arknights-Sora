#!/usr/bin/python3
'Arknights-Sora'
__author__ = 'zsppp'
__version__ = 'v1.1.0'

# python系统基础模块
import logging, sys, threading, time, traceback
from enum import Enum
# 连接安卓设备，点击等操作
from airtest.core.android.android import Android
from airtest.core.android.adb import ADB
from airtest.core.android.constant import CAP_METHOD, ORI_METHOD, TOUCH_METHOD
# cv2
import cv2

# adb 日志打印等级
(lambda logger:(logger.setLevel(logging.INFO),logger)[-1])(logging.getLogger('airtest')).handlers[0].formatter.datefmt='%H:%M:%S'
# 图片识别 日志打印等级
(lambda logger: (logger.setLevel(logging.DEBUG), logger.addHandler((lambda handler: (
handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s]<%(name)s> %(message)s', '%H:%M:%S')), handler)[
    -1])(logging.StreamHandler()))))(logging.getLogger('arknights'))
logger = logging.getLogger('arknights.Func')

# 点击坐标枚举 = x, y 坐标
class Click(Enum):
    CORNER =                  (1800, 1000)  # 界面右下角（开始行动）
    DRINK_SANITY =            (1634, 866)  # 喝理智液
    MENU =                    (410, 55)  # 菜单
    MENU_TASK =               (1630, 55)  # 菜单-任务
    MENU_TASK_WEEK =          (1450, 55)  # 菜单-任务-周常
    MENU_TASK_COLLECT =       (1600, 200)  # 菜单-任务-点击领取
    MENU_FRIEND =             (1800, 55)  # 菜单-好友
    MENU_FRIENDLIST =         (180, 340)  # 菜单-好友列表
    MENU_COMMUNICATION =      (1500, 250)  # 菜单-访问基建
    MENU_COMMUNICATION_NEXT = (1750, 950)  # 菜单-基建访问下位

# 图片枚举 = （文件路径， 匹配坐标， 匹配阈值（可选，默认0.1））
class Image(Enum):
    MENU =                  ('image/menu.png',                  (240, 5, 580, 110), .2)
    FRIEND_LIST =           ('image/friend_list.png',           (1600, 180, 1780, 320), .2)
    COMMUNICATION_NEXT =    ('image/communication_next.png',    (1600, 850, 1940, 940), .2)
    TASK_COLLECT =          ('image/task_collect.png',          (1480, 140, 1900, 280), .2)
    TASK_CLEAN =            ('image/task_clean.png',            (130, 220, 260, 290), .2)
    BATTLE_START_1 =        ('image/battle_start_1.png',        (1650, 940, 1870, 1030))
    BATTLE_START_2 =        ('image/battle_start_2.png',        (1530, 680, 1770, 920))
    BATTLE_CONTINUE =       ('image/battlecontinue.png',        (480, 920, 750, 1040), .2)
    SANITY_EMPTY =          ('image/sanity_empty.png',          (200, 440, 360, 560), .2)
    SANITY_DRUG =           ('image/sanity_drug.png',           (1020, 110, 1120, 200))
    AGENCY_ERROR =          ('image/agency_error.png',          (500, 650, 800, 800), .2)
    MISSION_FAILED =        ('image/mission_failed.png',        (150, 400, 650, 650))
    AGENCY_FLAG =           ('image/agency_flag.png',           (1500, 800, 1900, 950))

class Base():
    def __init__(self, serialno=None):
        logger.debug("Base init")
        self.lock = threading.Lock()
        self.terminate_flag = False
        self.suspend_flag = False
        self.serialno = None
        self.airtest = None
        if serialno:
            self.airtest_init(serialno)

    def __del__(self):
        logger.debug("Base delete")
        del self.airtest

    def get_devices(self):
        try:
            adb_list = [i for i,j in ADB().devices()if j=='device']
            index = adb_list.index(self.serialno)if self.serialno and self.serialno in adb_list else 0
            return adb_list, index
        except:
            traceback.print_exc()
            logger.error('Get devices failed!')
            return [], 0

    def airtest_init(self, serialno=None):
        if self.airtest:
            self.airtest_deinit()
        if serialno is None:
            adb_list, index = self.get_devices()
            if len(adb_list) > 0:
                serialno = adb_list[index]
            else:
                logger.error('No devices available!')
                return
        logger.info('启动 airtest ，尝试 adb 连接...')
        logger.info(f'ADB connect {serialno}')
        try:
            self.airtest = Android(serialno, cap_method=CAP_METHOD.JAVACAP, ori_method=ORI_METHOD.ADB,
                             touch_method=TOUCH_METHOD.MAXTOUCH)
        except:
            self.serialno = None
            self.airtest = None
            raise
        self.serialno = serialno

        self.render = [round(i) for i in self.airtest.get_render_resolution(True)]
        if self.render[2] * 9 > self.render[3] * 16:
            self.scale, self.border = (1080 / self.render[3], (round(self.render[2] - self.render[3] * 16 / 9) >> 1, 0)) 
        else:
            self.scale, self.border = (1920 / self.render[2], (0, round(self.render[3] - self.render[2] * 9 / 16) >> 1))       
        self.airtest.maxtouch.install_and_setup()
        # 载入点击信息
        self.click_map = {i: [round(i.value[j] / self.scale + self.border[j] + self.render[j]) for j in range(2)] for i in Click}
        # 载入图片信息
        self.image_map = {i: [cv2.imread(i.value[0]), i.value[1:]] for i in Image}

    def airtest_deinit(self):
        del self.airtest
        self.airtest = None
        self.serialno = None


    def __sleep(self, x, part=.1):
        timer = time.time() + x - part
        while True:
            while self.suspend_flag and not self.terminate_flag:
                time.sleep(.5)
            if self.terminate_flag:
                sys.exit(0)
            if time.time() >= timer:
                break
            time.sleep(part)
        time.sleep(max(0, timer + part - time.time()))

    def __click_coordinate(self, pos):
        logger.debug(pos)
        with self.lock:
            try:
                self.airtest.touch(pos)
            except:
                traceback.print_exc()
                logger.info('尝试重新启动airtest...')
                self.airtest_init(self.serialno)

    def __click(self, key, wait=500):
        logger.debug(key)
        self.__click_coordinate(self.click_map[key])
        self.__sleep(wait*.001)

    def __screen_shot(self, forwordLagency=.5, backwordLagency=.5):
        self.__sleep(forwordLagency)
        self.im = cv2.resize(
            self.airtest.snapshot()[
                self.render[1] + self.border[1]:self.render[1] + self.render[3] - self.border[1],
                self.render[0] + self.border[0]:self.render[0] + self.render[2] - self.border[0]], 
            (1920, 1080),
            interpolation=cv2.INTER_CUBIC)
        self.__sleep(backwordLagency)
        return True

    def __image_compare(self, img_key, click_flag=False):
        key_value = self.image_map[img_key]
        img = key_value[0]
        rect = key_value[1][0]
        threshold = .1 if len(key_value[1]) <= 1 else key_value[1][1]
        loc = cv2.minMaxLoc(cv2.matchTemplate(
            self.im[rect[1]:rect[3],
            rect[0]:rect[2]],
            img,
            cv2.TM_SQDIFF_NORMED
        ))
        value = loc[0]
        logger.debug(f'Compare {img_key}, {threshold > value}, value= {value}')
        if click_flag and threshold > value:
            self.__click_coordinate((rect[0]+loc[2][0]+(img.shape[1]>>1), rect[1]+loc[2][1]+(img.shape[0]>>1)))
        return threshold > value

    def __image_click(self, img_key):
        return self.__image_compare(img_key, True)

    def __image_wait(self, img, flag=True, wait=.5):
        while self.__screen_shot(wait, .5):
            if self.__image_compare(img) == flag:
                break


    # 由此往下的函数都是包含具体操作逻辑
    # 循环当前关卡，喝药清空理智
    def action_battle(self, battle_total='infinite', sanity_total=0):
        if self.airtest is None:
            return
        if isinstance(battle_total, int) and battle_total <= 0:
            battle_total = 'infinite'
        if not isinstance(sanity_total, int):
            sanity_total = 0
        battle_count, sanity_count = 0, 0
        logger.info('---------- arkFunc ------------------------')
        logger.info(f' Battle Total:{battle_total}, Sanity Total:{sanity_total}')
        logger.info('-------------------------------------------')

        def ui_level():
            while True:
                self.__screen_shot()
                if self.__image_compare(Image.SANITY_EMPTY):
                    return False
                elif self.__image_click(Image.BATTLE_START_1):
                    continue
                elif self.__image_click(Image.BATTLE_START_2):
                    break
                elif self.__image_compare(Image.BATTLE_CONTINUE):
                    break
                else:
                    logger.error('UI identified error')
                    return False
            return True
        def ui_sanity():
            nonlocal  sanity_count, sanity_total
            if sanity_count >= sanity_total:
                return False
            if not self.__image_compare(Image.SANITY_EMPTY):
                logger.error('UI identified error')
                return False
            if not self.__image_compare(Image.SANITY_DRUG):
                logger.info(f'Sanity lack {sanity_total - sanity_count}. Sanity Drug is not enough!!!')
                return False
            sanity_count += 1
            logger.info(f'Drink Sanity {sanity_count}/{sanity_total}')
            self.__click(Click.DRINK_SANITY, 0)
            self.__image_wait(Image.SANITY_DRUG, False)
            return True
        def ui_battle():
            self.__image_wait(Image.BATTLE_CONTINUE)
            logger.info('Battle Continue...')
            self.__image_wait(Image.BATTLE_CONTINUE, False, 3)
            self.__screen_shot(.5, .1)
            if self.__image_compare(Image.MISSION_FAILED):
                logger.info('行动失败')
                self.terminate_flag = True
        def ui_end():
            while True:
                self.__screen_shot()
                if self.__image_compare(Image.AGENCY_ERROR):
                    logger.info('代理失误')
                    self.terminate_flag = True
                if not self.__image_compare(Image.MENU):
                    self.__click(Click.CORNER, 400)
                else:
                    break
        self.__screen_shot()
        self.__image_click(Image.AGENCY_FLAG)
        # 主循环
        while True:
            if not ui_level():
                if not ui_sanity():
                    logger.info("---Sanity Empty")
                    self.__click(Click.CORNER, 0)
                    break
                else:
                    continue
            battle_count += 1
            logger.info(f'---Battle Start--- {battle_count}/{battle_total}')
            ui_battle()
            ui_end()
            if isinstance(battle_total, int) and battle_count >= battle_total:
                break
        logger.info(f'---Battle Finished--- total={battle_count}, cost time=')

    def action_task_reward(self):
        def collect():
            while True:
                self.__click(Click.MENU_TASK_COLLECT, 500)
                self.__click(Click.CORNER, 200)
                self.__screen_shot()
                if not self.__image_compare(Image.MENU):
                    continue
                elif self.__image_compare(Image.TASK_CLEAN):
                    logger.info("报酬已领取")
                    break
                elif not self.__image_compare(Image.TASK_COLLECT):
                    logger.info("尚有任务未完成")
                    break

        self.__screen_shot()
        logger.info("领取任务奖励...")
        self.__click(Click.MENU, 400)
        self.__click(Click.MENU_TASK, 1000)
        collect()
        self.__click(Click.MENU_TASK_WEEK, 500)
        collect()
        logger.info("任务领取完毕...")

    # 访问基建
    def action_communication(self):
        if self.airtest is None:
            return
        self.__click(Click.CORNER, 500)
        self.__screen_shot()
        if not self.__image_compare(Image.MENU):
            return
        self.__click(Click.MENU, 500)
        self.__click(Click.MENU_FRIEND, 200)
        self.__image_wait(Image.MENU)
        self.__click(Click.MENU_FRIENDLIST, 400)
        self.__image_wait(Image.FRIEND_LIST)
        self.__click(Click.MENU_COMMUNICATION, 400)
        logger.info("访问基建，线索交流...")
        while True:
            self.__click(Click.MENU_COMMUNICATION_NEXT, 1200)
            self.__screen_shot()
            if self.__image_compare(Image.MENU) and not self.__image_compare(Image.COMMUNICATION_NEXT):
                break
        logger.info("访问基建结束")
    
    # TODO
    def action_infastructure():
        logger.info("收取基建结束")

    # TODO
    def action_login(self):
        self.airtest.adb.cmd('shell am start -n com.hypergryph.arknights/com.u8.sdk.U8UnityContext')
        """
        while not image.login:
            click.corner
        image_click(image.login)
        """
        logger.info("登录界面")
    
    def action_test(self):
        self.__screen_shot()
        self.__image_click(Image.AGENCY_FLAG)

base = Base()

# sample
if __name__=='__main__':
    sanity = 0
    if len(sys.argv) >= 2:
        sanity = sys.argv[1]

    base.airtest_init()
    #base.action_login()
    base.action_battle(sanity_total=sanity)
    base.action_communication()
    base.action_task_reward()
