import localstack_client.session
import json
import pdb
import docker
from unittest.mock import patch
import os
import pytest
import pkg_resources
import neurocaas_interface.jobtools as jobtools
import neurocaas_interface.log as log
import neurocaas_interface.awstools as awstools 

loc = os.path.realpath(__file__)
testdir = os.path.dirname(loc)
root = os.path.realpath(os.path.join(testdir,"../"))
source = os.path.join(root,"neurocaas_interface")


@pytest.fixture(autouse = True)
def boto3_localstack_s3patch(monkeypatch):
    session_ls = localstack_client.session.Session()
    def mock_connect():
        """Mocks the s3 connect function in awstools function

        """
        return session_ls.resource("s3")
    monkeypatch.setattr(log, "s3_resource", session_ls.resource("s3"))
    monkeypatch.setattr(awstools, "s3_connect", mock_connect)

def create_mock_data(bucket_name,key,localdatapath):
    """Create arbitrary mock data at a path in localstack.
    """
    with open(localdatapath,"rb") as f:
        body = f.read()
    session_ls = localstack_client.session.Session()
    s3_localclient = session_ls.client("s3")
    s3_localclient.create_bucket(Bucket=bucket_name)
    s3_localclient.put_object(Bucket=bucket_name,Key = key,Body = body)

def empty_and_delete_bucket(bucket_name):
    """Delete a bucket in localstack. 
    """
    session_ls = localstack_client.session.Session()
    s3_localclient = session_ls.client("s3")
    s3_localresource = session_ls.resource("s3")
    bucket = s3_localresource.Bucket(bucket_name)
    bucket.objects.all().delete()
    s3_localclient.delete_bucket(Bucket=bucket_name)

certbucket = "caiman-ncap-web"
certkey = "reviewers/results/job__caiman-ncap-web_1589650394/logs/certificate.txt"
certpath = os.path.join("s3://",certbucket,certkey)
#localcertpath = "../src/neurocaas_contrib/template_mats/certificate.txt"
localcertpath = os.path.join(testdir,"test_mats","certificate.txt")
#localcertpath = pkg_resources.resource_filename("neurocaas_contrib","template_mats/certificate.txt")

statusbucket = "caiman-ncap-web"
statuskey = "reviewers/results/job__caiman-ncap-web_1589650394/logs/DATASET_NAME-dataset.ext_STATUS.txt.json"
statuspath = os.path.join("s3://",statusbucket,statuskey)
#localstatuspath = "../src/neurocaas_contrib/template_mats/DATASET_NAME-dataset.ext_STATUS.txt.json"
localstatuspath = os.path.join(testdir,"test_mats","DATASET_NAME-dataset.ext_STATUS.txt.json")

class Test_NeuroCAASJob(object):
    def test_NeuroCAASJob(self):
        bucket = "caiman-ncap-web"
        group = "reviewers"
        submit = {"dataname":"fakityfake","configname":"fakeityfake","timestamp":"1589650394","exitcode":0}
        create_mock_data(certbucket,certkey,localcertpath)
        jobtools.NeuroCAASJob(bucket,group,submit) 

    def test_NeuroCAASJob__parse_cert(self):
        bucket = "caiman-ncap-web"
        group = "reviewers"
        submit = {"dataname":"fakityfake","configname":"fakeityfake","timestamp":"1589650394","exitcode":0}
        create_mock_data(certbucket,certkey,localcertpath)
        job = jobtools.NeuroCAASJob(bucket,group,submit) 
        ## fill in this field that would be created by the run function
        job.resultspath  = os.path.join("s3://",job.bucket,job.group,"results","job__{b}_{ts}".format(b= job.bucket,ts = job.submit["timestamp"]))
        job._parse_cert()
        ids = [job.instances[i+1]["instance_id"] for i in range(9)]
        datasets = [job.instances[i+1]["dataset"] for i in range[9]]

