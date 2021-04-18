from .utils import *
import threading
import boto3

AWSREGIONS = ['us-east-2',
              'us-east-1',
              'us-west-1',
              'us-west-2',
              'af-south-1',
              'ap-east-1',
              'ap-south-1',
              'ap-northeast-3',
              'ap-northeast-2',
              'ap-southeast-1',
              'ap-southeast-2',
              'ap-northeast-1',
              'ca-central-1',
              'cn-north-1',
              'cn-northwest-1',
              'eu-central-1',
              'eu-west-1',
              'eu-west-2',
              'eu-south-1',
              'eu-west-3',
              'eu-north-1',
              'me-south-1',
              'sa-east-1']

def set_aws_keys(access_key,secret_key,region='us-east-1'):
    fname = CREDENTIALS_FILE
    cred = '''[default]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}
'''
    dirname = os.path.dirname(fname)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)    
    with open(fname,'w') as fd:
        fd.write(cred.format(access_key=access_key,secret_key = secret_key))
    fname = pjoin(os.path.expanduser('~'),'.aws','config')
    if not region is None:
        conf = '''[default]
region={region}'''
        with open(fname,'w') as fd:
            fd.write(conf.format(region=region))


def read_aws_keys(awscredfile = CREDENTIALS_FILE):
    awsfolder = pjoin(os.path.expanduser('~'),'.aws')
    awsconfig = pjoin(awsfolder,'config')
    access_key = ''
    secret_key = ''
    region = 'us-east-1'
    if os.path.isfile(awscredfile):
        with open(awscredfile,'r') as fd:
            for ln in fd:
                if 'aws_access_key_id' in ln:
                    ln = ln.split('=')
                    if len(ln)>1:
                        access_key = ln[-1].strip(' ').strip('\n')
                if 'aws_secret_access_key' in ln:
                    ln = ln.split('=')
                    if len(ln)>1:
                        secret_key = ln[-1].strip(' ').strip('\n')
    if os.path.isfile(awsconfig):
        with open(awsconfig,'r') as fd:
            for ln in fd:
                if 'region' in ln:
                    ln = ln.split('=')
                    region = ln[-1].strip(' ')
    return dict(access_key = access_key,
                secret_key = secret_key,
                region = region)


from boto3.s3.transfer import TransferConfig
multipart_config = TransferConfig(multipart_threshold=1024*25,
                                  max_concurrency=12,
                                  multipart_chunksize=1024*25,
                                  use_threads=True)

def s3_connect():
    aws = read_aws_keys()
    session = boto3.session.Session(aws_access_key_id = aws['access_key'],
                                    aws_secret_access_key = aws['secret_key'])
    return session, session.resource('s3'), session.client('s3')


def s3_ls(buckets, s3 = None, refreshfunc = None, **kwargs):
    '''
    List s3 files while refreshing the gui:
    s3_ls(s3_connect(), ['bucket1','bucket2'], refreshfunc = QApplication.processEvents)
    '''
    if s3 is None:
        session, s3, s3_client = s3_connect()
    files = []
    for bucketname in buckets:
        bucket = s3.Bucket(bucketname)
        for l in list(bucket.objects.all()):
            if not refreshfunc is None:
                refreshfunc()
            files.append(bucketname + '/' + l.key)
    return files


class UploadNonBlocking(threading.Thread):
    def __init__(self, filepath, destination, bucketname, s3 = None):
        super(Upload,self).__init__()
        self.s3 = s3
        statinfo = os.stat(filepath)
        self.fsize = statinfo.st_size
        self.count = 0
        self.isrunning = False
        self.bucketname = bucketname
        self.filepath = filepath
        self.destination = destination
        
    def run(self):
        if self.s3 is None:
            _, self.s3, _ = s3_connect()

        self.isrunning = True
        to_log('Upload: ' + self.filepath)
        def update(chunk):
            self.count += chunk
            self.isrunning = True
        bucket =self.s3.Bucket(self.bucketname)
        bucket.upload_file(self.filepath,
                           self.destination,
                           Callback = update,
                           Config = multipart_config)
        self.isrunning = False
