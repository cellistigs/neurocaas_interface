from .utils import *
from .awstools import *
import time
import tempfile

class NeuroCAASJob(threading.Thread):
    def __init__(self, bucket, group, submit,
                 uploadpath = None,
                 state = None,
                 config = None,
                 s3 = None):
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
        super(NeuroCAASJob,self).__init__()
        self.s3 = s3
        if state is None:
            state = 'init'
        self.count = 0
        self.isrunning = False
        self.bucket = bucket
        self.group = group
        self.uploadpath = uploadpath
        self.fsize = 0
        if not self.uploadpath is None:
            if os.path.isfile(self.uploadpath):
                statinfo = os.stat(filepath)
                self.fsize = statinfo.st_size
        self.submit = submit
        self.config = None
        self.state = state
        self.submitpath = None
        self.start()
    def run(self):
        if self.s3 is None: # this should be inside the thread.
            self.s3 = s3_connect()
        bucket = self.s3.Bucket(self.bucket)
                            
        self.isrunning = True
        while self.isrunning:
            if self.state == 'init':
                print(self.state)
                if self.uploadpath is None:
                    to_log('No datafile to upload.')
                else:
                    to_log('Upload: ' + self.uploadpath)
                    def update(chunk):
                        self.count += chunk
                        self.isrunning = True
                    bucket.upload_file(self.uploadpath,
                                       self.submit['dataname'],
                                       Callback = update,
                                       Config = multipart_config)
                self.state = 'uploaded'
            elif self.state == 'uploaded':
                print(self.state)
                if self.submit['timestamp'] is None:
                    self.submit['timestamp'] = time.strftime("%Y%m%d_%H%M%S")
                if not self.config is None:
                    # upload a config file
                    pass
                # make a temporary file, upload it to neurocaas and delete it
                with tempfile.NamedTemporaryFile(dir=NCAASTMP, delete=True) as tmpfile:
                    with open(tmpfile.name, 'w') as f:
                        json.dump(self.submit, f, indent=4, sort_keys=True)
                    self.submitpath = '{0}/submissions/{1}submit.json'.format(
                        self.group,
                        self.submit['timestamp']) 
                    bucket.upload_file(tmpfile.name,
                                       self.submitpath)

                to_log('Submitted job {0}'.format(self.submit['timestamp']))
                self.state = 'submitted'
            elif self.state == 'submitted':
                print(self.state)
                # check if the folder for this job exists in results
                self.state = 'started'
            elif self.state == 'started':
                print(self.state)
                # check for an 'end.txt' file
                self.state = 'completed'
            elif self.state == 'completed':
                # download the files and close
                self.isrunning = False
                print(self.state)
        self.isrunning = False
        print('Stopped.')
    def stop(self):
        self.isrunning = False
