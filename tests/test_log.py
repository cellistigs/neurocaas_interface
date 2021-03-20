import localstack_client.session
import json
import pdb
import docker
from unittest.mock import patch
import os
import pytest
import pkg_resources
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

#@pytest.fixture(scope = "class",params=["running","created","stopped","exited"])
#def test_containers(request):
#    """A fixture function to create docker containers for test purposes. The params given to this fixture function are strings specifying the container state: "running", "created", "exited", "stopped". 
#
#    """
#    if request.param == "running":
#        container = Test_NeuroCAASDataStatus.client.containers.run("neurocaas/contrib:base",
#                "/bin/bash -c 'while sleep 0.01; do ls; done'",
#                name = "datastatustest_running",
#                detach = True
#                )
#    elif request.param == "created": 
#        container = Test_NeuroCAASDataStatus.client.containers.create("neurocaas/contrib:base",
#                "/bin/bash -c 'while sleep 0.01; do ls; done'",
#                name = "datastatustest_created",
#                detach = True
#                )
#    elif request.param == "stopped": 
#        container = Test_NeuroCAASDataStatus.client.containers.create("neurocaas/contrib:base",
#                "/bin/bash -c 'while sleep 0.01; do ls; done'",
#                name = "datastatustest_created",
#                detach = True
#                )
#        container.stop()
#    elif request.param == "exited":
#        container = Test_NeuroCAASDataStatus.client.containers.run("neurocaas/contrib:base",
#                "/bin/bash -c 'ls'",
#                name = "datastatustest_exited",
#                detach = True
#                )
#    yield container
#    container.remove(force = True)


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

class Test_NeuroCAASCertificate(object):
    def test_NeuroCAASCertificate(self):
        create_mock_data(certbucket,certkey,localcertpath)
        ncc = log.NeuroCAASCertificate(certpath)
        assert ncc.writeobj.init_dict["loc"] == "s3"

    def test_NeuroCAASCertificate_write_default(self):
        with pytest.raises(AssertionError):
            ncc = log.NeuroCAASCertificate("s3://fake/path.txt")

    def test_NeuroCAASCertificate_process_rawcert(self):
        create_mock_data(certbucket,certkey,localcertpath)
        ncc = log.NeuroCAASCertificate(certpath)
        certdict,writedict,arange = ncc.process_rawcert(ncc.rawfile)
        assert list(sorted(certdict.keys())) == list(range(len(certdict.keys())))
        for wd in writedict.values():
            for k in wd.keys():
                assert k in ["dataname","line","linenb"]

    def test_NeuroCAASCertificate_get_instances(self):
        create_mock_data(certbucket,certkey,localcertpath)
        ncc = log.NeuroCAASCertificate(certpath)
        instances = ncc.get_instances()
        inst_list = ["i-0ffd013d096ff1ba6",'i-0568018e8e91f9d86','i-090fd859fb1896fbd','i-080d95e0a33f6c4e3','i-0855a2b4ff679f0e1','i-04fb53d7fd4654bc9','i-032edbe87f9fe16c4','i-06138dc2d1c1dcf85','i-063fe3454e97a453c']
        instance_list = [iv["id"] for iv in instances.values()]
        dataset = [iv["dataset"] for iv in instances.values()] 
        assert set(instance_list) == set(inst_list)
        assert set(dataset) == set(["raw_data.zip"]*9)

    def test_NeuroCAASCertificate_update_instance_info(self):
        updatedict = {"n":"groupname/inputs/dataname.ext"}
        base  = "DATANAME: groupname/inputs/dataname.ext | STATUS: N/A | TIME: N/A | LAST COMMAND: N/A | CPU_USAGE: N/A"
        ncc = log.NeuroCAASCertificate(certpath)
        ncc.update_instance_info(updatedict)
        update = ncc.certdict[2]
        assert base == update
        
    def test_NeuroCAASCertificate_update_instance_info_wrongname(self):
        updatedict = {"n":"randomname"}
        base  = "DATANAME: randomname | STATUS: N/A | TIME: N/A | LAST COMMAND: N/A | CPU_USAGE: N/A"
        ncc = log.NeuroCAASCertificate(certpath)
        ncc.update_instance_info(updatedict)
        update = ncc.certdict[2]
        assert base == update

    def test_NeuroCAASCertificate_update_instance_info_noname(self):
        updatedict = {"r":"random command"}
        base  = "DATANAME: N/A | STATUS: N/A | TIME: N/A | LAST COMMAND: random command | CPU_USAGE: N/A"
        ncc = log.NeuroCAASCertificate(certpath)
        ncc.update_instance_info(updatedict)
        update = ncc.certdict[2]
        assert base == update

    def test_NeuroCAASCertificate_update_instance_info_wrongloc(self):
        updatedict = {"n":"randomname"}
        base  = "DATANAME: randomname | STATUS: N/A | TIME: N/A | LAST COMMAND: N/A | CPU_USAGE: N/A"
        ncc = log.NeuroCAASCertificate(certpath)
        with pytest.raises(IndexError):
            ncc.update_instance_info(updatedict,loc = 10)

    def test_NeuroCAASCertificate_write(self):
        ncc = log.NeuroCAASCertificate(certpath)
        ncc.write()


class Test_NeuroCAASDataStatus():
    client = docker.from_env()
    @classmethod
    def setup_class(cls):
        """setup a docker container that's just printing every second. Equivalent to the command:
            docker run -it neurocaas/contrib:base /bin/bash -c 'while sleep 1; do ls; done'
        """
        create_mock_data("caiman-ncap-web","reviewers/results/job__caiman-ncap-web_1589650394/logs/DATASET_NAME-dataset.ext_STATUS.txt.json",localstatuspath)

    @classmethod
    def teardown_class(cls):    
        empty_and_delete_bucket("caiman-ncap-web")

    def test_NeuroCAASDataStatus(self):
        create_mock_data(statusbucket,statuskey,localstatuspath)
        ncds = log.NeuroCAASDataStatus(statuspath,None)
        assert ncds.writeobj.init_dict["loc"] == "s3" 

    def test_NeuroCAASDataStatus_get_default_rawfile(self):    
        create_mock_data(statusbucket,statuskey,localstatuspath)
        ncds = log.NeuroCAASDataStatus(statuspath,None)
        assert type(ncds.rawfile) == dict

    @pytest.mark.xfail
    def test_NeuroCAASDataStatus_get_stdout(self):    
        create_mock_data(statusbucket,statuskey,localstatuspath)
        ncds = log.NeuroCAASDataStatus(statuspath,None)
        output = ncds.get_stdout()
        assert type(output) == list
        assert type(output[0]) == str 
    
    @pytest.mark.xfail
    def test_NeuroCAASDataStatus_get_status(self):
        create_mock_data(statusbucket,statuskey,localstatuspath)
        ncds = log.NeuroCAASDataStatus(statuspath,None)
        status = ncds.get_status()

    @pytest.mark.xfail
    def test_NeuroCAASDataStatus_get_usage(self):
        create_mock_data(statusbucket,statuskey,localstatuspath)
        ncds = log.NeuroCAASDataStatus(statuspath,test_containers)
        usagedict = ncds.get_usage()
        for key in usagedict.keys():
            assert key in ["cpu_total","memory_total_mb"]
        for value in usagedict.values():
            assert type(value) in [int,float,str]
        assert usagedict["cpu_total"] >= 0 
        
    @pytest.mark.xfail
    def test_NeuroCAASDataStatus_update_file(self,test_containers): 
        create_mock_data(statusbucket,statuskey,localstatuspath)
        ncds = log.NeuroCAASDataStatus(statuspath,test_containers)
        ncds.update_file()

    @pytest.mark.xfail
    def test_NeuroCAASDataStatus_write_local(self,test_containers):
        with pytest.raises(AssertionError):
            ncds = log.NeuroCAASDataStatus("s3://fake.ext",test_containers)

    @pytest.mark.xfail
    def test_NeuroCAASDataStatus_write_s3(self,monkeypatch,test_containers):
        create_mock_data(statusbucket,statuskey,localstatuspath)
        def teststdout(garbage):
            return ["std 0","std 1","std 2"]
        monkeypatch.setattr(log.NeuroCAASDataStatus,"get_stdout",teststdout)
        ncds = log.NeuroCAASDataStatus(statuspath,test_containers)
        ncds.update_file()
        ncds.write()
        self.session_ls = localstack_client.session.Session()
        s3_localclient = self.session_ls.client("s3")
        remote = self.session_ls.resource("s3").Object(statusbucket,statuskey).get()["Body"].read().decode("utf-8")
        datadict = json.loads(remote)
        for key in datadict:
            assert datadict[key] == ncds.rawfile[key]


class Test_WriteObj():
    def setup_method(self):
        self.bucket_name = "test-writeobj-bucket"
        self.session_ls = localstack_client.session.Session()
        s3_localclient = self.session_ls.client("s3")
        s3_localclient.create_bucket(Bucket=self.bucket_name)
    def test_WriteObj_local(self):
        localpath = os.path.join(testdir,"test_mats/object.txt") 
        init_dict = {"loc":"local","localpath":localpath}
        wo = log.WriteObj(init_dict)
    def test_WriteObj_s3(self):
        key = "object.txt"
        init_dict = {"loc":"s3","bucket":self.bucket_name,"key":key}
        wo = log.WriteObj(init_dict)
    def test_WriteObj_put_local(self):
        localpath = os.path.join(testdir,"test_mats/object.txt") 
        init_dict = {"loc":"local","localpath":localpath}
        wo = log.WriteObj(init_dict)
        wo.put("text")
    def test_WriteObj_put_s3(self):
        key = "object.txt"
        init_dict = {"loc":"s3","bucket":self.bucket_name,"key":key}
        wo = log.WriteObj(init_dict)
        wo.put("text")
    def test_WriteObj_put_consistent(self):
        key = "object.txt"
        localpath = os.path.join(testdir,"test_mats/object.txt") 
        init_dict1 = {"loc":"s3","bucket":self.bucket_name,"key":key}
        init_dict2 = {"loc":"local","localpath":localpath}
        wo1 = log.WriteObj(init_dict1)
        wo2 = log.WriteObj(init_dict2)
        text = "text"
        wo1.put(text)
        wo2.put(text)
        with open(localpath,"rb") as f:
            local = f.read().decode("utf-8")
        remote = self.session_ls.resource("s3").Object(self.bucket_name,key).get()["Body"].read().decode("utf-8")
        assert local == remote == text
    def test_WriteObj_put_json_local(self):    
        key = "object.txt"
        localpath = os.path.join(testdir,"test_mats/object.txt") 
        init_dict = {"loc":"local","localpath":localpath}
        wo = log.WriteObj(init_dict)
        data_dict = {"a":"aa","b":"bb"}
        wo.put_json(data_dict)
        with open(localpath) as f:
            data = json.load(f)
            
        for k in data_dict:    
            assert data_dict[k] == data[k]

        
    def teardown_method(self):
        s3_localclient = self.session_ls.client("s3")
        s3_localresource = self.session_ls.resource("s3")
        bucket = s3_localresource.Bucket(self.bucket_name)
        bucket.objects.all().delete()
        s3_localclient.delete_bucket(Bucket=self.bucket_name)


