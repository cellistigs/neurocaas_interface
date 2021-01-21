# NeuroCAAS Local Interface for efficient data transfer. 

## Info for Joao: 
### General Testing Stack Structure
The interface can be tested at the bucket ***cianalysispermastack***. I have added your website enabled credentials (jcouto) to the group ***traviscipermagroup***, allowing you to upload datasets in the corresponding bucket.  

The bucket has the following structure: 

```bash 

s3://cianalysispermastack
|-traviscipermagroup 
  |-inputs
    |-dataset1.json
    |-dataset2.json
  |-configs
    |-config_None_None.json
    |-config.json
    |-...
  |-submissions
    |-submit.json
    |-condition_0_0submit.json
    |-...
  |-results
    |-job__cianalysispermastack_23:05:47.219155condition_0_2/
      |-logs/
      |-process_results/
        |-end.txt/
```

We can run many different test cases in this stack, but I will focus on the simplest one for now. 

### Paths to monitor 

In the simplest case, we can trigger a job by uploading a submit file that looks like this:

```json
{
"dataname":"traviscipermagroup/inputs/dataset1.json",
"configname": "traviscipermagroup/configs/config_None_None.json",
"timestamp": "value_text"}
```

Here the dataname and configname fields refer to data and config files that exist in the inputs and configs directories. The interesting part is the `timestamp` field: this dictates a location in the results directory where job results will be written. In particular, if timestamp has a value "value\_text", then the job results will be written to "s3://cianalysispermastack/traviscipermagroup/results/job\_\_cianalysispermastack\_value\_text/". I usually monitor for this location to be created to start showing users logs (which are updated live) and results. 
To monitor for the end of the job, I have configured analyses available through the website to create a subdirectory "process\_results", and to write a file end.txt when the job is finished. 

In brief, I monitor for the directory `{bucketname}/{groupname}/job__{bucketname}_{timestamp}` to start showing users job data, and file `{bucketname}/{groupname}/job__{bucketname}_{timestamp}/process_results/end.txt` to signal job completion.  

You can find an example submit file that should work in this repo at [./files/condition_test_interface_submit.json](./files/condition_test_interface_submit.json) 

