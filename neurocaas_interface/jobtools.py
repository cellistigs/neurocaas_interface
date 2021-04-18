from .utils import *
from .awstools import *
from .log import NeuroCAASCertificate, NeuroCAASDataStatus
import time
import tempfile

class NeuroCAASJob(threading.Thread):
    def __init__(self, bucket, group, submit,
                 uploadpath = None,
                 localpath = None
                 state = None,
                 config = None,
                 s3 = None,
                 post_func = lambda x: print(x.submitpath)):
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
        self.client = None
        self.session = None

        self.instances = []
        self.files = []        

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
        self.download_dir = localpath
        self.results = None        
        self.endlog = None
        
        self.start()
    def run(self):
        if self.s3 is None: # this should be inside the thread.
            self.session,self.s3,self.client = s3_connect()
        bucket = self.s3.Bucket(self.bucket)
                            
        self.isrunning = True
        while self.isrunning:
            if self.state == 'init':
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
                ## parse into the results folder name here:
                self.resultsprefix = "{g}/results/job__{b}_{ts}".format(
                    b = self.bucket, g = self.group, ts = self.submit["timestamp"])
                self.resultspath = "s3://{b}/{g}/results/job__{b}_{ts}/".format(
                    b = self.bucket, g = self.group, ts = self.submit["timestamp"])
                self.endpath = "s3://{b}/{g}/results/job__{b}_{ts}/".format(
                    b = self.bucket, g = self.group, ts = self.submit["timestamp"])
            elif self.state == 'submitted':
                self.check_results_path()
                if len(list(filter(lambda x: 'certificate.txt' in x,jb.files))):
                    self.state = 'started'
            elif self.state == 'started':
                self.check_results_path()
                if len(list(filter(lambda x: 'end.txt' in x,jb.files))):
                    self.state = 'finished'
                    # check for an 'end.txt' file
            elif self.state == 'finished':
                # download the files and close
                self.state = 'post'
            elif self.state == 'post':
                # download the files and close
                self.post_func(self)
                self.state = 'completed'
            elif self.state == 'completed' and not self.post_func is None:
                self.isrunning = False
        self.isrunning = False
        
    def _parse_cert(self):
        """Parses the certificate file and assigns here along with a dictionary specifying instance info. This info is as follows: 
        {instance_number:{dataset:dataset_name,id:instance_id},} with the instance_number index starting at 1. 

        """
        if not self.resultspath is None:
            self.cert = NeuroCAASCertificate(self.resultspath+"logs/certificate.txt")
            self.instances = self.cert.get_instances()

    def check_results_path(self):
        # populate the files
        files = self.client.list_objects_v2(Bucket=self.bucket,Prefix = self.resultsprefix)
        if 'Contents' in files.keys():
            self.files = [f['Key'] for f in files['Contents']]
            
    def stop(self):
        # this stops the thread but remote jobs keep running
        self.isrunning = False

    def stop_job(self):
        for instance in self.instances:
            # delete 
            pass
