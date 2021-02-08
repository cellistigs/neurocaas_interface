from .utils import *
from .awstools import *
import time

class RemoteNeuroCAASJob(threading.Thread):
    def __init__(self, uploadpath, bucket, submit, state = None, config = None, s3 = None):
        '''
        RemoteJob

        Submits a job to NeuroCAAS an monitors progress

**uploadpath** is the path to the file to upload

**submit** is a dictionary with fields:
  - dataname   : path on aws for the data file
  - configname : path for the config file
  - timestamp  : path to monitor (None is auto)
  - exitcode   : 0 ??

**state** is the name of the bucket
        '''
        super(RemoteNeuroCAASJob,self).__init__()
        self.s3 = s3
        if self.s3 is None:
            self.s3 = s3_connect()
        if state is None:
            state = 'init'
        self.count = 0
        self.isrunning = False
        self.bucket = bucket
        self.uploadpath = uploadpath
        self.fsize = None
        if os.path.isfile(self.uploadpath):
            statinfo = os.stat(filepath)
            self.fsize = statinfo.st_size
        self.submit = submit
        self.config = None
        self.state = state
        
    def run(self):
        self.isrunning = True
        while self.isrunning:
            if self.state == 'init':
                to_log('Upload: ' + self.uploadpath)
                def update(chunk):
                    self.count += chunk
                    self.isrunning = True
                bucket = self.s3.Bucket(self.bucket)
                bucket.upload_file(self.uploadpath,
                                   self.submit['dataname'],
                                   Callback = update,
                                   Config = multipart_config)
                self.state = 'uploaded'
            elif self.state == 'uploaded':
                if self.submit['timestamp'] is None:
                    self.submit['timestamp'] = time.strftime("%Y_%m_%d_%H:%M:%S")
                if not self.config is None:
                    # upload a config file
                    pass
                # make a temporary file, upload it to neurocaas and delete it
                to_log('Submitting job {0}'.format(self.submit['timestamp']))
                self.state = 'submitted'
            elif self.state == 'submitted':
                # check if the folder for this job exists in results
                self.state = 'started'
            elif self.state == 'started':
                # check for an 'end.txt' file
                self.state = 'completed'
            elif self.state == 'completed':
                # download the files and close
                self.isrunning = False
        self.isrunning = False

    def stop(self):
        self.isrunning = False
