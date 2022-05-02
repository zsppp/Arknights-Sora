# python系统基础模块
import logging,os,sys,threading
# Qt，界面依赖模块
import PyQt5
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,pyqtSignal,QUrl
from PyQt5.QtWidgets import QApplication,QMainWindow,QInputDialog,QMessageBox
# Music
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent
# 识别图片和操作游戏界面的逻辑
import arkFunc
# Qt Designer设计界面，使用命令由ui转换成py文件，eg: pyuic5 xx.ui -o xx.py
from arkMainWindow import Ui_arkMainWindow
# 配置信息
from config import Config

logger = logging.getLogger('arknights.Gui')

class MyMainWindow(QMainWindow):
    signalFuncBegin = pyqtSignal()
    signalFuncEnd = pyqtSignal()
    def __init__(self,parent=None):
        logger.info('正在启动...')
        super().__init__(parent)
        self.ui = Ui_arkMainWindow()
        self.ui.setupUi(self)
        self.configLoad()
        self.setDebug()
        self.arkFuncInit()
        self.thread = threading.Thread()
        self.signalFuncBegin.connect(self.funcBegin)
        self.signalFuncEnd.connect(self.funcEnd)
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile('music/end.mp3')))
        self.player.setVolume(15)
        logger.info('OK!')

    def configLoad(self):
        config_default = {
            'serialno':         None,
            'music_flag':       False,
            'clue_flag':        True,
            'debug_flag':       False,
            }
        config_ui_map = {
            'music_flag':       self.ui.CB_MUSIC.setChecked,
            'clue_flag':        self.ui.CB_CLUE.setChecked,
            'debug_flag':       self.ui.MENU_SETTINGS_DEBUG.setChecked,
            }
        self.config = Config(config_default, 'config/config.json')
        for key, func in config_ui_map.items():
            func(self.config[key])

    def arkFuncInit(self, serialno=None):
        """
        if self.config['serialno']:
            serialno = self.config['serialno']
        """
        if serialno and serialno == arkFunc.base.serialno:
            return
        self.config['serialno'] = None
        arkFunc.base.airtest_init(serialno)
        if arkFunc.base.serialno != None:
            self.config['serialno'] = arkFunc.base.serialno

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
        if arkFunc.base.terminate_flag:
            logger.info('程序终止...')
        # 播放结束音乐
        if self.ui.CB_MUSIC.isChecked() and not arkFunc.base.terminate_flag: 
            self.player.play()
            logger.info('end music~')
        self.ui.TXT_BATTLECOUNT.setValue(0)
        self.ui.TXT_SANITYCOUNT.setValue(0)
        app.alert(self, 0)

    # 获取adb devices
    def getDevice(self):
        adbList, index = arkFunc.base.get_devices()
        text,ok = QInputDialog.getItem(self,'选取设备','在下拉列表中选择一个设备', adbList, index, True,Qt.WindowStaysOnTopHint)
        if ok and text:
            self.arkFuncInit(text)

    def adbConnect(self):
        text,ok = QInputDialog.getText(self,'连接设备','远程设备地址',text='localhost:5555')
        if ok and text:
            self.arkFuncInit(text)

    # 检查截图
    def checkSnapShot(self):arkFunc.base.show()if arkFunc.base.serialno else QMessageBox.critical(self,'错误','未连接设备')

    def pwsHere(self):
        if 'win' in sys.platform:
            os.system('start PowerShell -NoLogo')

    def closeEvent(self,event):
        if self.thread.is_alive()and QMessageBox.warning(self,'关闭','战斗正在进行,确认关闭?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:
            event.ignore()
            return
        arkFunc.base.terminate_flag = True
        if not self.thread._started:self.thread.join()

    def runMain(self):
        if arkFunc.base.serialno is None:
            QMessageBox.critical(self,'错误','未连接设备')
            return

        def f():
            try:
                self.signalFuncBegin.emit()
                arkFunc.base.suspend_flag = False
                arkFunc.base.terminate_flag = False
                arkFunc.action_battle(self.ui.TXT_BATTLECOUNT.value(), self.ui.TXT_SANITYCOUNT.value())
                if self.ui.CB_CLUE.isChecked():
                    arkFunc.action_communication()
                arkFunc.action_task_reward()
            finally:
                self.signalFuncEnd.emit()
        self.thread = threading.Thread(target=f, name='arkFunc')
        self.thread.start()

    def stop(self):
        arkFunc.base.terminate_flag = True

    # TODO
    def setMusic(self):
        self.config['music_flag'] = self.ui.CB_MUSIC.isChecked()

    # TODO
    def setClue(self):
        self.config['clue_flag'] = self.ui.CB_CLUE.isChecked()

    def setDebug(self):
        flag = self.ui.MENU_SETTINGS_DEBUG.isChecked()
        self.config['debug_flag'] = flag
        logLevel = logging.DEBUG if flag else logging.INFO
        logging.getLogger('airtest').setLevel(logLevel)
        logging.getLogger('arknights').setLevel(logLevel)

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

# QWidget: Must construct a QApplication before a QWidget 使用Qt库前需要调用QApplication
app=QApplication(sys.argv)

if __name__=='__main__':
    myWin = MyMainWindow()
    myWin.setWindowIcon(QIcon("image/gui/Sora.ico"))
    myWin.show()
    sys.exit(app.exec_())
