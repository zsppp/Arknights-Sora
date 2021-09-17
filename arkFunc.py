'Arknights-Sora'
__author__ = 'zsppp'
__version__ = 'v1.0.7'

# python系统基础模块
import logging, os, sys, threading, time, operator, traceback
# 连接安卓设备，点击等操作
from airtest.core.android.android import Android
from airtest.core.android.adb import ADB
from airtest.core.android.constant import CAP_METHOD, ORI_METHOD, TOUCH_METHOD
# cv2
import cv2

#adb 日志打印等级
(lambda logger:(logger.setLevel(logging.INFO),logger)[-1])(logging.getLogger('airtest')).handlers[0].formatter.datefmt='%H:%M:%S'
#图片识别 日志打印等级
(lambda logger: (logger.setLevel(logging.INFO), logger.addHandler((lambda handler: (
handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s]<%(name)s> %(message)s', '%H:%M:%S')), handler)[
    -1])(logging.StreamHandler()))))(logging.getLogger('arknights'))
logger = logging.getLogger('arknights.Func')

# 用于暂停和退出
terminateFlag = False
suspendFlag = False


def sleep(x, part=.1):
    timer = time.time() + x - part
    while True:
        while suspendFlag and not terminateFlag:
            time.sleep(.5)
        if terminateFlag:
            sys.exit(0)
        if time.time() >= timer:
            break
        time.sleep(part)
    time.sleep(max(0, timer + part - time.time()))


class Base(Android):
    def __init__(self, serialno=None):
        self.lock = threading.Lock()
        if serialno is None:
            self.serialno = None
            return
        try:
            super().__init__(serialno, cap_method=CAP_METHOD.JAVACAP, ori_method=ORI_METHOD.ADB,
                             touch_method=TOUCH_METHOD.MAXTOUCH)
        except:
            self.serialno = None
        else:
            self.render = [round(i) for i in self.get_render_resolution(True)]
            self.scale, self.border = (
                1080 / self.render[3],
                (round(self.render[2] - self.render[3] * 16 / 9) >> 1, 0)) \
                if self.render[2] * 9 > self.render[3] * 16 else \
                (1920 / self.render[2], (0, round(self.render[3] - self.render[2] * 9 / 16) >> 1))
            self.maxtouch.install_and_setup()
            self.key = {
                c: [round(p[i] / self.scale + self.border[i] + self.render[i]) for i in range(2)] for c, p in {
                    ' ': (1800, 1000),  # 界面右下角（开始行动）
                    'B': (1650, 750),  # 开始战斗
                    'Y': (1634, 866),  # 喝理智液
                    'H': (410, 55), # 菜单
                    'M': (1630, 55), # 菜单-任务
                    'W': (1450, 55), # 菜单-任务-周常
                    'C': (1600, 200), # 菜单-任务-点击领取
                    'F': (1800, 55), # 菜单-好友
                    'L': (180, 340), # 菜单-好友列表
                    'I': (1500, 250), # 菜单-访问基建
                    'N': (1750, 950), # 菜单-基建访问下位

                }.items()}
    def press(self, c):
        logger.debug(f'press {c}')
        with self.lock:
            '''
            try:
                super().touch(self.key[c])
            except Exception as err:
                traceback.print_exc()
                raise err
            '''
            super().touch(self.key[c])
            
    def perform(self,pos,wait):
        [(self.press(i),sleep(j*.001))for i,j in zip(pos,wait)]

    def snapShot(self):
        return cv2.resize(
            super().snapshot()[
                self.render[1] + self.border[1]:self.render[1] + self.render[3] - self.border[1],
                self.render[0] + self.border[0]:self.render[0] + self.render[2] - self.border[0]
            ], (1920, 1080),
            interpolation=cv2.INTER_CUBIC)

    def adbDisconnect(self):
        if self.serialno:
            self.adb.disconnect()
    '''
    def adbReconnect(self):
        if self.serialno:
            self.adb.disconnect()
            del self.adb
            self.adb = ADB(self.serialno)
    '''
base = Base()

# 载入识别图片
IMG_HOME = cv2.imread('image/home.png')
IMG_FRIENDLIST = cv2.imread('image/friendlist.png')
IMG_CLICKTOCOLLECT = cv2.imread('image/clicktocollect.png')
IMG_CLICKTOCOMMUNICATION = cv2.imread('image/clicktocommunication.png')
IMG_COLLECTCLEAN = cv2.imread('image/collectclean.png')
IMG_BATTLEPREPARE = cv2.imread('image/battleprepare.png')
IMG_BATTLEBEGIN = cv2.imread('image/battlebegin.png')
IMG_BATTLECONTINUE = cv2.imread('image/battlecontinue.png')
IMG_COMMANDER = cv2.imread('image/commander.png')
IMG_SANITYEMPTY = cv2.imread('image/sanityempty.png')
IMG_SANITYDRUG = cv2.imread('image/sanitydrug.png')
check = None


class Check:
    def __init__(self, forwordLagency=.01, backwordLagency=0):
        sleep(forwordLagency)
        self.im = base.snapShot()
        global check
        check = self
        sleep(backwordLagency)

    def show(self):
        cv2.imshow('Check Screenshot - Press S to save', cv2.resize(self.im, (0, 0), fx=.4, fy=.4))
        if cv2.waitKey() == ord('s'):
            self.save()
        cv2.destroyAllWindows()
        return self

    def compare(self, img, imgname, rect=(0, 0, 1920, 1080), threshold=.1):
        value = cv2.minMaxLoc(cv2.matchTemplate(
            self.im[rect[1]:rect[3],
            rect[0]:rect[2]],
            img,
            cv2.TM_SQDIFF_NORMED
        ))[0]
        if not operator.eq(imgname, "NOT_PRINT"):
            logger.debug(f'Compare {imgname} {value}')
        return threshold > value

    def detect(self,img,rect=(0,0,1920,1080),threshold=.05):
        loc = (cv2.minMaxLoc(cv2.matchTemplate(self.im[rect[1]:rect[3],rect[0]:rect[2]],img,cv2.TM_SQDIFF_NORMED)))
        logger.debug(f'detect {loc[0]}')
        return loc[0]<threshold

    def tap(self,img,rect=(0,0,1920,1080),threshold=.05):
        return(lambda loc:loc[0]<threshold and base.touch(rect[0]+loc[2][0]+(img.shape[1]>>1), rect[1]+loc[2][1]+(img.shape[0]>>1)))(cv2.minMaxLoc(cv2.matchTemplate(self.im[rect[1]:rect[3],rect[0]:rect[2]],img,cv2.TM_SQDIFF_NORMED)))

    #主页
    def isHome(self):
        return self.compare(IMG_HOME, "IMG_Home", (240, 5, 580, 110), .2)

    #查看名片，确定当前界面是好友列表
    def isFriendList(self):
        return self.compare(IMG_FRIENDLIST, "IMG_FriendList", (1600, 180, 1780, 320), .2)

    #一键领取
    def isClickToCollect(self):
        return self.compare(IMG_CLICKTOCOLLECT, "IMG_ClickToCollect", (1480, 140, 1900, 280), .2)

    #访问基建
    def isClickToCommunication(self):
        return self.compare(IMG_CLICKTOCOMMUNICATION, "IMG_ClickToCommunication", (1600, 850, 1940, 940), .2)

    #报酬已领取
    def isCollectClean(self):
        return self.compare(IMG_COLLECTCLEAN, "IMG_CollectClean", (130, 220, 260, 290), .2)

    def isBattlePrepare(self):
        return self.compare(IMG_BATTLEPREPARE, "IMG_BattlePrepare", (1650, 940, 1870, 1030))

    def isBattleBegin(self):
        return self.compare(IMG_BATTLEBEGIN, "IMG_BattleBegin", (1530, 680, 1770, 920))

    def isBattleContinue(self):
        return self.compare(IMG_BATTLECONTINUE, "IMG_BattileContinue", (890, 175, 1030, 225), .2)

    def isActingCommander(self):
        return self.compare(IMG_COMMANDER, "IMG_ActingCommander", (480, 920, 750, 1040), .2)

    def isSanityEmpty(self):
        return self.compare(IMG_SANITYEMPTY, "IMG_SANITYEMPTY", (200, 440, 360, 560), .2)

    def isSanityDrug(self):
        return self.compare(IMG_SANITYDRUG, "IMG_SANITYDRUG", (1020, 110, 1120, 200))


def Battle(battleTotal=-1, sanityTotal=0):
    def drinkSanity():
        nonlocal sanityCount, sanityTotal
        if sanityCount < sanityTotal:
            if check.isSanityDrug():
                sanityCount += 1
                logger.info(f'Drink Sanity {sanityCount}/{sanityTotal}')
                base.press("Y")
                #不同显卡渲染画面稍有差异，导致isBattlePrepare图片匹配失败卡住；暂时解决方法：添加多一个判断
                while True:
                    if Check(.5, .5).isBattlePrepare() or not check.isSanityDrug():
                        break
                return True
            else:
                logger.info(f'Sanity {sanityCount}/{sanityTotal},lack {sanityTotal - sanityCount}. Sanity Drug is not enough!!!')
                return False

    battleCountInfo = 'infinite'
    if battleTotal > 0:
        battleCountInfo = battleTotal
    logger.info('------arkFunc------------------------')
    logger.info(f' Battle Count:{battleCountInfo}, Sanity Count:{sanityTotal}')
    logger.info('-------------------------------------')
    battleCount, sanityCount = 0, 0
    while True:
        # 行动前后逻辑
        while True:
            Check(.5, .5)
            if check.isBattleContinue():
                break
            elif check.isSanityEmpty():
                if not drinkSanity():
                    logger.info("---Sanity Empty")
                    base.press(" ")
                    return
            elif check.isBattlePrepare():
                base.press(" ")
            elif check.isBattleBegin():
                base.press("B")
                break
            else:
                base.press(" ")
            logger.debug(" ")
        # 开始行动
        battleCount += 1
        logger.info(f'---Battle Start {battleCount}')
        # 持续判断行动进行
        while True:
            Check(.5,.5)
            if check.isBattleContinue() or check.isActingCommander():
                break
        logger.info('Battle Continue...')
        while True:
            Check(.5,3)
            if not (check.isBattleContinue() or check.isActingCommander()):
                break
        #战斗结束后的处理
        if battleTotal > 0:
            logger.info(f'Battle Finished {battleCount}/{battleTotal}')
            if battleCount >= battleTotal:
                logger.info("---Battle Complete")
                for i in range(5):
                    Check(.5,.5)
                    if check.isHome():
                        break
                    base.press(" ")
                return
        else:
            logger.info('Battle Finished')

def DailyWork(clue_en = 0):
    def judgeUI():
        if not Check(.5,.5).isHome():
            base.press(" ")
            if not Check(1,.1).isHome():
                return False
        return True

    def clickToCollect():
        while True:
            base.perform("C ",(500,200))
            Check()
            if not check.isHome():
                continue
            if check.isCollectClean():
                logger.info("报酬已领取")
                break
            if not check.isClickToCollect():
                logger.info("尚有任务未完成")
                break
        return

    def clickToCommunication():
        while True:
            base.perform("N",(1200,))
            Check()
            if check.isHome() and not check.isClickToCommunication():
                break
        return


    if not judgeUI():
        logger.error("无法识别当前界面")
        return
    logger.info("领取任务奖励...")
    base.perform("HM",(400,1000))
    clickToCollect()
    base.perform("WWWW",(400,400,400,400))
    clickToCollect()
    logger.info("任务领取完毕...")

    #TODO 考虑添加每日只领取一次线索的限制，避免溢出线索浪费
    if clue_en:
        if not judgeUI():
            logger.error("无法识别当前界面")
            return
        while True:
            base.perform("HF", (400, 100))
            if judgeUI():
                break
        base.perform("L", (400,))
        for i in range(3):
            if Check(0.5,).isFriendList():
                base.perform("I", (400,))
                logger.info("访问基建，线索交流...")
                clickToCommunication()
                break

    logger.info("清理结束")
    return

#测试图片匹配
def Test():
    Check(.5,.5).isBattleContinue()
    check.isActingCommander()
    return
