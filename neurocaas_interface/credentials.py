from .utils import *
from .awstools import *
from  PyQt5.QtWidgets import (QDockWidget,
                              QWidget,
                              QGridLayout,
                              QTabWidget,
                              QFormLayout,
                              QLabel,
                              QPlainTextEdit,
                              QLineEdit,
                              QComboBox,
                              QDialogButtonBox,
                              QVBoxLayout)
from PyQt5 import QtCore
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except:
    print('Could not load QWebEngineView - The credential manager will not work.')


class CredentialsManager(QDockWidget):
    def __init__(self,
                 configfile = NEUROCAAS_CONFIG_PATH):
        '''
        Logs to NeuroCAAS to retrieve the keys and 
allows changing the config parameters and credentials 
from the GUI.
        '''
        super(CredentialsManager,self).__init__()
        self.awsinfo = read_aws_keys()
        self.ncaasconfig = read_config()
        ncaasconfig_json = json.dumps(self.ncaasconfig,
                                      indent=4,
                                      sort_keys=True)
        self.configfile = configfile
        
        mainw = QWidget()
        self.setWidget(mainw)
        layout = QGridLayout()
        mainw.setLayout(layout)
        
        self.setWindowTitle('NeuroCAAS configuration')

        tabwidget = QTabWidget()
        layout.addWidget(tabwidget,0,0)

        advancedwid = QWidget()
        lay = QFormLayout()
        advancedwid.setLayout(lay)

        self.cred_access = QLineEdit(self.awsinfo['access_key'])
        lay.addRow(QLabel('AWS access key'),self.cred_access)
        def cred_access():
            self.awsinfo['access_key'] = self.cred_access.text()
        self.cred_access.textChanged.connect(cred_access)

        self.cred_secret = QLineEdit(self.awsinfo['secret_key'])
        lay.addRow(QLabel('AWS secret key'),self.cred_secret)
        def cred_secret():
            self.awsinfo['secret_key'] = self.cred_secret.text()
        self.cred_secret.textChanged.connect(cred_secret)

        self.aws_region = QComboBox()
        for r in AWSREGIONS:
            self.aws_region.addItem(r)
        self.aws_region.setCurrentIndex(AWSREGIONS.index(self.awsinfo['region']))
        lay.addRow(QLabel('AWS region'),self.aws_region)
        def region_call(value):
            self.awsinfo['region'] = AWSREGIONS[value]    
        self.aws_region.currentIndexChanged.connect(region_call)
        
        self.configedit = QPlainTextEdit(ncaasconfig_json)
        lay.addRow(QLabel('NCAAS settings'),self.configedit)
        w = QWidget()
        l = QVBoxLayout()
        w.setLayout(l)
        lab = QLabel('Log to neurocaas.org and go to the user settings page to get the credentials.')
        l.addWidget(lab)
        web = QWebEngineView()
        l.addWidget(web)
        web.load(QtCore.QUrl(NEUROCAAS_LOGIN_URL))
        tabwidget.addTab(w,'NeuroCAAS login')
        tabwidget.addTab(advancedwid,'Settings')

        self.html = ''
        def parsehtml():
            page = web.page()
            def call(var):
                self.html = var
                tt = var.split('\n')
                values = []
                extra = '<input class="form-control" type="text" value="'
                for i,t in enumerate(tt):
                    if extra in t:
                        values.append(t.replace(extra,'').strip(' ').split('"')[0])
                if len(values)>=4:
                    self.cred_access.setText(values[2])
                    self.cred_secret.setText(values[3])
                    print('Got credentials from the website, you can close this window.')
                    dlg = QDialog()
                    dlg.setWindowTitle('Great!')
                    but = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    def ok():
                        self.close()
                        dlg.accept()
                    but.accepted.connect(ok)
                    but.rejected.connect(dlg.accept)
                    l = QVBoxLayout()
                    lab = QLabel('Got the credentials from the website, you can now close this window to continue. Or adjust defaults in the Advanced tab')
                    lab.setStyleSheet("font: bold")
                    l.addWidget(lab)
                    l.addWidget(but)
                    dlg.setLayout(l)
                    dlg.exec_()
                    
            page.toHtml(call)
        web.loadFinished.connect(parsehtml)
        def setHtml(self,html):
            self.html = html
        self.show()
    def closeEvent(self,event):
        set_aws_keys(**self.awsinfo)
        try:
            from io import StringIO
            pars = json.load(StringIO(self.configedit.toPlainText()))
            with open(self.configfile,'w') as fd:
                json.dump(pars,fd,indent=4,sort_keys = True)
        except Exception as E:
            print('Error in the configuration file, did not save')
            return
        event.accept()



