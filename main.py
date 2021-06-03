#python系统基础模块
import logging,os,sys,threading,time
#连接安卓设备，点击等操作
import airtest
from airtest.core.android.adb import ADB
#Qt，界面依赖模块
import PyQt5
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,pyqtSignal,QUrl
from PyQt5.QtWidgets import QApplication,QMainWindow,QInputDialog,QMessageBox
#music
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent
#识别图片和操作安卓的逻辑
import arkFunc
#Qt Designer设计界面，使用命令由ui转换成py文件，eg: pyuic5 xx.ui -o xx.py
from arkMainWindow import Ui_arkMainWindow

logger=logging.getLogger('arknights.Gui')
endMusic='music/end.mp3'

#QWidget: Must construct a QApplication before a QWidget 使用Qt库前需要调用QApplication
app=QApplication(sys.argv)

class MyMainWindow(QMainWindow):
    signalFuncBegin=pyqtSignal()
    signalFuncEnd=pyqtSignal()
    def __init__(self,parent=None):
        logger.info('正在启动...')
        super().__init__(parent)
        self.ui=Ui_arkMainWindow()
        self.ui.setupUi(self)
        self.getDevice()
        self.thread=threading.Thread()
        self.signalFuncBegin.connect(self.funcBegin)
        self.signalFuncEnd.connect(self.funcEnd)
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(endMusic)))
        self.player.setVolume(15)
        logger.info('OK!')
    def funcBegin(self):
        self.ui.BIN_START.setEnabled(False)
        self.ui.TXT_BATTLECOUNT.setEnabled(False)
        self.ui.TXT_SANITYCOUNT.setEnabled(False)
        self.ui.BIN_STOP.setEnabled(True)
    def funcEnd(self):
        self.ui.BIN_START.setEnabled(True)
        self.ui.TXT_BATTLECOUNT.setEnabled(True)
        self.ui.TXT_SANITYCOUNT.setEnabled(True)
        self.ui.BIN_STOP.setEnabled(False)
        if arkFunc.terminateFlag:
            logger.info('程序终止...')
        #播放结束音乐
        if self.ui.CB_MUSIC.isChecked() and not arkFunc.terminateFlag: 
            self.player.play()
            logger.info('end music~')
        self.ui.TXT_BATTLECOUNT.setValue(0)
        self.ui.TXT_SANITYCOUNT.setValue(0)
        app.alert(self, 0)
    #获取adb devices
    def getDevice(self):
        text,ok=(lambda adbList:QInputDialog.getItem(self,'选取设备','在下拉列表中选择一个设备',adbList,adbList.index(arkFunc.base.serialno)if arkFunc.base.serialno and arkFunc.base.serialno in adbList else 0,True,Qt.WindowStaysOnTopHint))([i for i,j in ADB().devices()if j=='device'])
        if ok and text and text!=arkFunc.base.serialno:arkFunc.base=arkFunc.Base(text)
    def adbConnect(self):
        text,ok=QInputDialog.getText(self,'连接设备','远程设备地址',text='localhost:5555')
        if ok and text:ADB(text)
    #检查截图
    def checkCheck(self):arkFunc.Check().show()if arkFunc.base.serialno else QMessageBox.critical(self,'错误','未连接设备')
    def pwsHere(self):os.system('start PowerShell -NoLogo')
    def closeEvent(self,event):
        if self.thread.is_alive()and QMessageBox.warning(self,'关闭','战斗正在进行,确认关闭?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:
            event.ignore()
            return
        arkFunc.terminateFlag=True
        if not self.thread._started:self.thread.join()
        arkFunc.base.adbDisconnect()
    def runMain(self):
        if not arkFunc.base.serialno:return QMessageBox.critical(self,'错误','未连接设备')
        battleCount=-1
        if self.ui.TXT_BATTLECOUNT.value()>0:
            battleCount=self.ui.TXT_BATTLECOUNT.value()
        def f():
            try:
                self.signalFuncBegin.emit()
                arkFunc.suspendFlag=False
                arkFunc.terminateFlag=False
                #任务清单
                arkFunc.Battle(battleCount, self.ui.TXT_SANITYCOUNT.value())
                arkFunc.DailyWork()
                #arkFunc.Test()
            finally:
                self.signalFuncEnd.emit()
        self.thread=threading.Thread(target=f,name='arkFunc')
        self.thread.start()
    def stop(self):arkFunc.terminateFlag=True
    def about(self):QMessageBox.about(self,'关于',f'''
<h2>Arknights-Sora</h2>
<table border="0">
  <tr>
    <td>当前版本</td>
    <td>{arkFunc.__version__}</td>
  </tr>
  <tr>
    <td>作者</td>
    <td>zsppp</td>
  </tr>
  <tr>
    <td>项目地址</td>
    <td><a href="https://github.com/zsppp/Arknights-Sora">https://github.com/zsppp/Arknights-Sora</a></td>
  </tr>
</table>
<br>
<br>
''')


if __name__=='__main__':
    myWin=MyMainWindow()
    myWin.setWindowIcon(QIcon("image/gui/Sora.ico"))
    myWin.show()
    sys.exit(app.exec_())
