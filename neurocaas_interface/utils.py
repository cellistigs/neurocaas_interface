import os
from os.path import join as pjoin
import json

NCAASDIR = pjoin(os.path.expanduser('~'),'.neurocaas')

NEUROCAAS_LOGIN_URL = "http://www.neurocaas.org/profile/"
NEUROCAAS_CONFIG_PATH = pjoin(NCAASDIR,'neurocaas_config.json')

def to_log(msg,logfile = None):
    '''
    Log actions and events to the neurocaas folder.

    to_log(msg, log_file_descriptor)
    
    '''
    if logfile is None:
        logfile = open(pjoin(
                     NCAASDIR,'neurocaas_log.txt'),'a')
    nmsg = '['+datetime.today().strftime('%y-%m-%d %H:%M:%S')+'] - ' + msg + '\n'
    logfile.seek(os.SEEK_END)
    logfile.write(nmsg)
    return nmsg

def tail(filename, nlines=100):
    """
    This needs work (should not read the whole file).
    """
    with open(filename,'r') as f:
        lines = f.readlines()
    if len(lines) > 100:
        lines = lines[-100:]
    return lines

defaultconfig = dict(buckets = ['cianalysispermastack'])

def read_config():
    if not os.path.exists(os.path.dirname(NEUROCAAS_CONFIG_PATH)):
        os.makedirs(os.path.dirname(NEUROCAAS_CONFIG_PATH))
    if not os.path.exists(NEUROCAAS_CONFIG_PATH):
        with open(NEUROCAAS_CONFIG_PATH,'w') as f:
            print('Creating config from defaults [{0}]'.format(NEUROCAAS_CONFIG_PATH))
            json.dump(defaultconfig, f,
                      indent = 4,
                      sort_keys = True)
    with open(NEUROCAAS_CONFIG_PATH,'r') as f:
        config = json.load(f)
        for k in config.keys():
            if k in defaultconfig.keys(): # Use default (2 levels down)
                if type(defaultconfig[k]) is dict: 
                    for j in defaultconfig[k].keys():
                        if not j in config[k].keys():
                            config[k][j] = defaultconfig[k][j]
            else:
                config[k] = defaultconfig[k]
    return config
