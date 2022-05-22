#!/usr/bin/python3
'Arknights-Sora'
__author__ = 'zsppp'
__version__ = 'v1.1.5'

# python系统基础模块
import logging, sys, threading, time, traceback
import datetime, numpy
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
handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s]<%(name)s><line %(lineno)s> %(message)s', '%H:%M:%S')), handler)[
    -1])(logging.StreamHandler()))))(logging.getLogger('arknights'))
logger = logging.getLogger('arknights.Func')

# 点击坐标枚举 = x, y 坐标
class Click(Enum):
    CORNER =                    (1800, 1000)  # 界面右下角（开始行动）
    DRINK_SANITY =              (1634, 866)  # 喝理智液
    MENU =                      (410, 55)  # 菜单
    MENU_TASK =                 (1630, 55)  # 菜单-任务
    MENU_TASK_WEEK =            (1450, 55)  # 菜单-任务-周常
    MENU_TASK_COLLECT =         (1600, 200)  # 菜单-任务-点击领取
    MENU_FRIEND =               (1800, 55)  # 菜单-好友
    MENU_FRIENDLIST =           (180, 340)  # 菜单-好友列表
    MENU_COMMUNICATION =        (1500, 250)  # 菜单-访问基建
    MENU_COMMUNICATION_NEXT =   (1750, 950)  # 菜单-基建访问下位
    MENU_TERMINAL =             (800, 300)
    CLOSE_SCHEDULE =            (1800, 130)
    LAST_BATTLE =               (1650, 877)

# 图片枚举 = （文件路径， 匹配坐标， 匹配阈值（可选，默认0.1））
class Image(Enum):
    MENU =                  ('image/menu.png',                  (240, 5, 580, 110), .2)
    FRIEND_LIST =           ('image/friend_list.png',           (1600, 180, 1780, 320), .2)
    COMMUNICATION_NEXT =    ('image/communication_next.png',    (1600, 850, 1940, 940), .2)
    COMMUNICATION_MAX =     ('image/communication_max.png',     (1400, 100, 1650, 300), .2)
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
    LOGIN =                 ('image/login.png',                 (800, 700, 1150, 850))
    TERMINAL =              ('image/terminal.png',              (1340, 160, 1580, 300))
    BATTLE_WEEK =           ('image/battle_week.png',           (1400, 140, 1800, 250))
    AP =                    ('image/ap.png',             (0, 0, 1920, 1080))
    LS =                    ('image/ls.png',             (0, 0, 1920, 1080))

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
                return False
        logger.info('启动 airtest ，adb 连接...')
        logger.info(f'adb connect {serialno}')
        try:
            self.airtest = Android(serialno, cap_method=CAP_METHOD.JAVACAP, ori_method=ORI_METHOD.ADB,
                             touch_method=TOUCH_METHOD.MAXTOUCH)
        except:
            self.serialno = None
            self.airtest = None
            logger.info('adb connect failed!')
            return False
        self.serialno = serialno
        logger.info('adb connect successed.')

        self.render = [round(i) for i in self.airtest.get_render_resolution(True)]
        if self.render[2] * 9 > self.render[3] * 16:
            self.scale, self.border = (1080 / self.render[3], (round(self.render[2] - self.render[3] * 16 / 9) >> 1, 0))
        else:
            self.scale, self.border = (1920 / self.render[2], (0, round(self.render[3] - self.render[2] * 9 / 16) >> 1))
        logger.info(f'render: {self.render}')
        logger.info(f'border: {self.border}')
        logger.info(f'scale: {self.scale}')
        logger.info(f'region: {self.render[1] + self.border[1]}, {self.render[1] + self.render[3] - self.border[1]}')
        logger.info(f'region: {self.render[0] + self.border[0]}, {self.render[0] + self.render[2] - self.border[0]}')
        logger.info(f'snapshot size: {self.airtest.snapshot().size}')
        self.airtest.maxtouch.install_and_setup()
        # 载入点击信息
        self.click_map = {i: [round(i.value[j] / self.scale + self.border[j] + self.render[j]) for j in range(2)] for i in Click}
        # 载入图片信息
        self.image_map = {i: [cv2.imread(i.value[0]), i.value[1:]] for i in Image}
        self.screen_shot(0,0)
        return True

    def airtest_deinit(self):
        del self.airtest
        self.airtest = None
        self.serialno = None

    def __airtest_restart(self):
        self.sleep(.1)
        traceback.print_exc()
        logger.info('尝试重新启动airtest...')
        self.airtest_init(self.serialno)

    def sleep(self, x, part=.1):
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

    def swipe(self,rect): # If this doesn't work, use the above one instead
        p1,p2=[numpy.array(self.airtest._touch_point_by_orientation([rect[i<<1|j]/self.scale+self.border[j]+self.render[j]for j in range(2)]))for i in range(2)]
        logger.debug(f"{p1} {p2}")
        vd=p2-p1
        lvd=numpy.linalg.norm(vd)
        vd/=.2*self.scale*lvd
        vx=numpy.array([0.,0.])
        def send(method,pos):self.airtest.touch_proxy.handle(' '.join((method,'0',*[str(i)for i in self.airtest.touch_proxy.transform_xy(*pos)],'50\nc\n')))
        with self.lock:
            send('d',p1)
            time.sleep(.01)
            for _ in range(2):
                send('m',p1+vx)
                vx+=vd
                time.sleep(.02)
            vd*=5
            while numpy.linalg.norm(vx)<lvd:
                send('m',p1+vx)
                vx+=vd
                time.sleep(.008)
            send('m',p2)
            time.sleep(1)#time.sleep(.35)
            self.airtest.touch_proxy.handle('u 0\nc\n')
            time.sleep(.02)#time.sleep(.02)

    def click(self, pos):
        logger.debug(pos)
        with self.lock:
            while True:
                try:
                    self.airtest.touch(pos)
                    break
                except:
                    self.__airtest_restart()
                    continue
    def click_by_pos(self, pos, wait=500):
        self.click(pos)
        self.sleep(wait*.001)

    def click_by_map(self, key, wait=500):
        logger.debug(key)
        self.click(self.click_map[key])
        self.sleep(wait*.001)

    def show(self):
        cv2.imshow('Check Screenshot - Press S to save',cv2.resize(self.im,(0,0),fx=.4,fy=.4))
        if cv2.waitKey()==ord('s'):
            cv2.imwrite(time.strftime(f'snapshot/Capture_%Y-%m-%d_%H.%M.%S.png',time.localtime(self.snapshot_timestamp)),self.im)
        cv2.destroyAllWindows()

    def screen_shot(self, forwordLagency=.9, backwordLagency=.1):
        self.sleep(forwordLagency)
        while True:
            try:
                self.im = cv2.resize(
                    self.airtest.snapshot()[
                        self.render[1] + self.border[1]:self.render[1] + self.render[3] - self.border[1],
                        self.render[0] + self.border[0]:self.render[0] + self.render[2] - self.border[0]], 
                    (1920, 1080),
                    interpolation=cv2.INTER_CUBIC)

                self.snapshot_timestamp = time.time()
                self.sleep(backwordLagency)
                break
            except:
                self.__airtest_restart()
                continue
        return True

    def image_compare(self, img_key, click_flag=False):
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
        if threshold < value:
            return False
        if click_flag:
            self.click((rect[0]+loc[2][0]+(img.shape[1]>>1), rect[1]+loc[2][1]+(img.shape[0]>>1)))
        return True

    def image_click(self, img_key, block_flag=False):
        ret=self.image_compare(img_key, True)
        if block_flag == True:
            while not ret:
                self.screen_shot(.5, .1)
                ret=self.image_compare(img_key, True)
        return ret

    def image_wait(self, img, flag=True, wait=.5):
        while self.screen_shot(wait, .5):
            if self.image_compare(img) == flag:
                break
    

def display_time(sec, granularity=3):
    intervals = (
                ('weeks', 604800),  # 60 * 60 * 24 * 7
                ('days', 86400),    # 60 * 60 * 24
                ('hours', 3600),    # 60 * 60
                ('minutes', 60),
                ('seconds', 1),
                )
    sec = int(sec)
    result = []
    for name, count in intervals:
        value = sec // count
        if value:
            sec -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])



# 由此往下都是游戏操作逻辑
# 循环当前关卡，喝药清空理智
def action_battle(battle_total='infinite', sanity_total=0):
    if base.airtest is None:
        return
    if isinstance(battle_total, int) and battle_total <= 0:
        battle_total = 'infinite'
    if not isinstance(sanity_total, int):
        sanity_total = 0
    battle_count, sanity_count = 0, 0
    logger.info('---------- arkFunc ------------------------')
    logger.info(
        f' Battle Total:{battle_total}, Sanity Total:{sanity_total}')
    logger.info('-------------------------------------------')

    def ui_start():
        fail_count = 0
        while True:
            base.screen_shot()
            if base.image_compare(Image.SANITY_DRUG):
                return False
            elif base.image_click(Image.BATTLE_START_1):
                continue
            elif base.image_click(Image.BATTLE_START_2):
                break
            elif base.image_compare(Image.BATTLE_CONTINUE):
                break
            else:
                if fail_count > 10:
                    logger.error('UI identified error')
                    return False
                fail_count += 1
                base.click_by_map(Click.CORNER)
        return True

    def ui_sanity():
        nonlocal sanity_count, sanity_total
        if sanity_count >= sanity_total:
            return False
        #if not base.image_compare(Image.SANITY_EMPTY):
            #logger.error('UI identified error')
            #return False
        if not base.image_compare(Image.SANITY_DRUG):
            logger.info(
                f'Sanity lack {sanity_total - sanity_count}. Sanity Drug is not enough!!!')
            return False
        sanity_count += 1
        logger.info(f'Drink Sanity {sanity_count}/{sanity_total}')
        base.click_by_map(Click.DRINK_SANITY, 0)
        base.image_wait(Image.SANITY_DRUG, False)
        return True

    def ui_battle():
        base.image_wait(Image.BATTLE_CONTINUE)
        logger.info('Battle Continue...')
        base.image_wait(Image.BATTLE_CONTINUE, False, 3)
        base.screen_shot(.5, .1)
        if base.image_compare(Image.MISSION_FAILED):
            logger.info('行动失败')
            base.terminate_flag = True

    def ui_end():
        while True:
            base.screen_shot()
            if base.image_compare(Image.AGENCY_ERROR):
                logger.info('代理失误')
                base.terminate_flag = True
            #if not base.image_compare(Image.MENU):
                #base.click_by_map(Click.MENU, 400)
            else:
                break
    begin_time = time.perf_counter()
    base.screen_shot()
    base.image_click(Image.AGENCY_FLAG)
    # 主循环
    while True:
        if not ui_start():
            if not ui_sanity():
                logger.info("---Sanity Empty")
                for i in range(3):
                    base.screen_shot()
                    if base.image_compare(Image.MENU):
                        break
                    base.click_by_map(Click.MENU, 500)
                break
            else:
                continue
        battle_count += 1
        logger.info(f'---Battle Start--- {battle_count}/{battle_total}')
        ui_battle()
        ui_end()
        if isinstance(battle_total, int) and battle_count >= battle_total:
            break
    end_time = time.perf_counter()
    logger.info(f'---Battle Finished--- total= {battle_count}, cost time= {display_time(end_time-begin_time)}')

#领取每日任务
def action_task_reward():
    if base.airtest is None:
        return
    def collect():
        while True:
            base.click_by_map(Click.MENU_TASK_COLLECT, 500)
            base.click_by_map(Click.CORNER, 200)
            base.screen_shot()
            if not base.image_compare(Image.MENU):
                continue
            elif base.image_compare(Image.TASK_CLEAN):
                logger.info("报酬已领取")
                break
            elif not base.image_compare(Image.TASK_COLLECT):
                logger.info("尚有任务未完成")
                break
    base.screen_shot()
    logger.info("领取任务奖励...")
    base.click_by_map(Click.MENU, 800)
    base.click_by_map(Click.MENU_TASK, 1000)
    collect()
    base.click_by_map(Click.MENU_TASK_WEEK, 500)
    collect()
    logger.info("任务领取完毕...")

# 访问基建
def action_communication():
    if base.airtest is None:
        return
    base.screen_shot()
    if not base.image_compare(Image.MENU):
        return
    base.click_by_map(Click.MENU, 800)
    base.click_by_map(Click.MENU_FRIEND, 200)
    base.image_wait(Image.MENU)
    base.click_by_map(Click.MENU_FRIENDLIST, 400)
    base.image_wait(Image.FRIEND_LIST)
    base.click_by_map(Click.MENU_COMMUNICATION, 400)
    logger.info("访问基建，线索交流...")
    while True:
        base.click_by_map(Click.MENU_COMMUNICATION_NEXT, 1200)
        base.image_wait(Image.MENU)
        if base.image_compare(Image.COMMUNICATION_MAX):
            break
        if not base.image_compare(Image.COMMUNICATION_NEXT):
            break
    logger.info("访问基建结束")

# TODO
def action_infastructure():
    if base.airtest is None:
        return
    logger.info("收取基建结束")

# 启动游戏
def action_login():
    if base.airtest is None:
        return
    # 添加检测手机是否锁屏

    logger.info("启动明日方舟")
    base.airtest.adb.cmd('shell am start -n com.hypergryph.arknights/com.u8.sdk.U8UnityContext')
    base.screen_shot(3)
    login = False
    # TODO 进入主界面需要等大概1s才有每日签到弹出
    while True:
        base.screen_shot()
        if base.image_compare(Image.MENU):
            break
        if base.image_click(Image.TERMINAL):
            continue
        if not login and base.image_click(Image.LOGIN):
            login = True
        base.click_by_map(Click.CLOSE_SCHEDULE) if login else base.click_by_map(Click.CORNER)

def action_schedule():
    now = datetime.datetime.now()
    w = now.weekday()
    week_list = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    logger.info(f"{now.strftime('%Y-%m-%d %H:%M:%S')}, 今天是{week_list[w]}")

    def goto_battle(goto_battle_area):
        if base.airtest is None:
            return
        base.screen_shot()
        if not base.image_compare(Image.MENU):
            return
        # TODO if not battle terminal
        base.click_by_map(Click.MENU, 800)
        base.click_by_map(Click.MENU_TERMINAL, 2000)
        base.image_wait(Image.MENU)
        goto_battle_area()
        action_battle()

    # 进入上次作战关卡
    #last_battle = lambda : base.click_by_map(Click.LAST_BATTLE, 1500)
    def last_battle():
        base.click_by_map(Click.LAST_BATTLE, 1500)
    # 每周剿灭
    def week_battle():
        base.image_click(Image.BATTLE_WEEK, True)

    def goto_resource(img):
        base.click_by_pos((1080, 1000), 1000)
        base.image_wait(Image.MENU)
        ret = base.image_click(img)
        if not ret:
            logger.debug("swipe left")
            base.swipe((500,900,1500,900))
            base.screen_shot()
            ret = base.image_click(img)
        if not ret:
            logger.debug("swipe right")
            base.swipe((1500,900,500,900))
            base.screen_shot()
            ret = base.image_click(img)
        if not ret:
            logger.error(f"{img} not find")
        return ret

    # TODO 进入芯片本，先锋、辅助
    def PR_C_2():
        base.click_by_pos((1080, 1000), 1000)
    # TODO 进入芯片本，近卫、特种
    def PR_D_2():
        base.click_by_pos((1080, 1000), 1000)
    # TODO 进入战术演习
    def LS_5():
        if goto_resource(Image.LS):
            base.image_wait(Image.MENU)
            base.click_by_pos((1466, 441), 100)
            base.click_by_pos((1466, 441), 500)
    # TODO 进入红票
    def AP_5():
        if goto_resource(Image.AP):
            base.image_wait(Image.MENU)
            base.click_by_pos((1405, 265), 100)
            base.click_by_pos((1405, 265), 500)
   
    schedule_list = [
                        (AP_5, ),
                        (LS_5, ),
                        (LS_5, ),
                        (AP_5, ),
                        (LS_5, ),
                        (AP_5, ),
                        (AP_5, ),
                    ]
    # 按照周计划进入不同的材料关卡
    if False:
        [goto_battle(i) for i in schedule_list[w]]
    # 进入上一次作战关卡
    else:
        goto_battle(last_battle)
    action_communication()
    action_task_reward()

base = Base()
# arkFunc.py sample
if __name__=='__main__':
    """
    sanity = 0
    if len(sys.argv) >= 2:
        sanity = int(sys.argv[1])
    """
    while base.airtest_init() == False:
        logger.info('wait adb server...')
        time.sleep(3)
    #base.screen_shot()
    #base.image_click(Image.AGENCY_FLAG)
    #exit(0)
    action_login()
    action_schedule()

