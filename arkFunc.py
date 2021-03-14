'Arknights-Sora'
__author__='zsppp'
__version__='v1.0.1'
#python系统基础模块
import logging,os,sys,threading,time,operator,builtins
#连接安卓设备，点击等操作
from airtest.core.android.android import Android
from airtest.core.android.constant import CAP_METHOD,ORI_METHOD,TOUCH_METHOD
#cv2
import cv2

(lambda logger:(logger.setLevel(logging.INFO),logger.addHandler((lambda handler:(handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s]<%(name)s> %(message)s','%H:%M:%S')),handler)[-1])(logging.StreamHandler()))))(logging.getLogger('ark'))
logger=logging.getLogger('ark.Func')

#用于暂停和退出
terminateFlag=False
suspendFlag=False
def sleep(x,part=.1):
    timer=time.time()+x-part
    while True:
        while suspendFlag and not terminateFlag:time.sleep(.5)
        if terminateFlag:builtins.exit(0)
        if time.time()>=timer:break
        time.sleep(part)
    time.sleep(max(0,timer+part-time.time()))

class Base(Android):
    def __init__(self,serialno=None):
        self.lock=threading.Lock()
        if serialno is None:
            self.serialno=None
            return
        try:super().__init__(serialno,cap_method=CAP_METHOD.JAVACAP,ori_method=ORI_METHOD.ADB,touch_method=TOUCH_METHOD.MAXTOUCH)
        except:self.serialno=None
        else:
            self.render=[round(i)for i in self.get_render_resolution(True)]
            self.scale,self.border=(1080/self.render[3],(round(self.render[2]-self.render[3]*16/9)>>1,0))if self.render[2]*9>self.render[3]*16 else(1920/self.render[2],(0,round(self.render[3]-self.render[2]*9/16)>>1))
            self.maxtouch.install_and_setup()
            self.key={c:[round(p[i]/self.scale+self.border[i]+self.render[i])for i in range(2)]for c,p in{
                ' ':(1846,1030),#右下角
                'B':(1650,750),#开始战斗
                'Y':(1634,866),#喝理智液
                }.items()}
    def press(self,c):
        logger.debug(f'press {c}')
        with self.lock:super().touch(self.key[c])
    def snapshot(self):return cv2.resize(super().snapshot()[self.render[1]+self.border[1]:self.render[1]+self.render[3]-self.border[1],self.render[0]+self.border[0]:self.render[0]+self.render[2]-self.border[0]],(1920,1080),interpolation=cv2.INTER_CUBIC)
base=Base()

#载入识别图片
IMG_BATTLEPREPARE=cv2.imread('image/battleprepare.png')
IMG_BATTLEBEGIN=cv2.imread('image/battlebegin.png')
IMG_BATTLECONTINUE=cv2.imread('image/battlecontinue.png')
IMG_SANITYEMPTY=cv2.imread('image/sanityempty.png')
IMG_SANITYDRUG=cv2.imread('image/sanitydrug.png')
check=None
class Check:
    def __init__(self,forwordLagency=.01,backwordLagency=0):
        sleep(forwordLagency)
        self.im=base.snapshot()
        global check
        check=self
        sleep(backwordLagency)
    def show(self):
        cv2.imshow('Check Screenshot - Press S to save',cv2.resize(self.im,(0,0),fx=.4,fy=.4))
        if cv2.waitKey()==ord('s'):self.save()
        cv2.destroyAllWindows()
        return self
    def compare(self,img,imgname,rect=(0,0,1920,1080),threshold=.1):
        value=cv2.minMaxLoc(cv2.matchTemplate(self.im[rect[1]:rect[3],rect[0]:rect[2]],img,cv2.TM_SQDIFF_NORMED))[0]
        if not operator.eq(imgname,"NOT_PRINT"):
            logger.debug(f'Compare {imgname} {value}')
        return threshold>value
    def isBattlePrepare(self):return self.compare(IMG_BATTLEPREPARE,"IMG_BATTLEPREPARE",(1670,960,1850,1010))
    def isBattleBegin(self):return self.compare(IMG_BATTLEBEGIN,"IMG_BATTLEBEGIN",(1553,701,1758,900))
    def isBattleContinue(self):return self.compare(IMG_BATTLECONTINUE,"NOT_PRINT",(890,175,1030,225),.2)
    def isSanityEmpty(self):return self.compare(IMG_SANITYEMPTY,"IMG_SANITYEMPTY",(205,455,340,540),.2)
    def isSanityDrug(self):return self.compare(IMG_SANITYDRUG,"IMG_SANITYDRUG",(1044,127,1108,184))

def main(battleCount=-1,sanityCount=0):
    def drinkSanity():
        nonlocal sanity,sanityCount
        if sanity<sanityCount:
            if check.isSanityDrug():
                sanity+=1
                logger.info(f'Drink Sanity {sanity}/{sanityCount}')
                base.press("Y")
                while True:
                    if Check(.5,.5).isBattlePrepare():break
                return True
            else:
                logger.info(f'Sanity {sanity}/{sanityCount},lack {sanityCount-sanity}. Sanity Drug is not enough!!!')
                return False

    battleCountInfo='infinite'
    if battleCount > 0:battleCountInfo=battleCount
    logger.info('-----arkFunc-----')
    logger.info(f' Battle Count:{battleCountInfo}, Sanity Count:{sanityCount}')
    logger.info('-----------------')
    battle,sanity=0,0
    while True:
        #行动前后逻辑
        while True:
            Check(.8,.2)
            if check.isBattleContinue():break
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
            else:base.press(" ")
            logger.debug(" ")
        #开始行动
        battle+=1
        logger.info(f'---Battle Start {battle}')
        #持续判断行动进行
        while True:
            if Check(.5,.5).isBattleContinue():break
        logger.info('Battle Continue...')
        while True:
            if not Check(.5,3).isBattleContinue():break
        if battleCount>0:
            logger.info(f'Battle Finished {battle}/{battleCount}')
            if battle>=battleCount:
                logger.info("---Battle Complete")
                base.press(" ")
                return
        else:logger.info('Battle Finished')
        

            

