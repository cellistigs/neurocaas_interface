from .utils import * 
from .jobtools import NeuroCAASJob
from ipywidgets import widgets
from IPython.display import display
from tqdm.notebook import tqdm_notebook



class nbNeuroCAASJob(NeuroCAASJob):
    def __init__(self, bucket, group, submit,
                 uploadpath = None,
                 localpath = None,
                 state = None,
                 config = None,
                 s3 = None,
                 post_func = lambda x: print(x.submitpath)):
    
        super(nbNeuroCAASJob,self).__init__(bucket = bucket,
                                            group = group,
                                            submit=submit,
                                            uploadpath = uploadpath,
                                            localpath = localpath,
                                            state = state,
                                            config = config,
                                            s3 = s3,
                                            update_func = self.update,
                                            post_func = post_func)
        if self.fsize>0:
            self.pbar = tqdm_notebook(desc = 'Upload',
                                      unit = 'MB',
                                      total = int(self.fsize/1024**2))
            self.pbar_last = 0
        self.wstate = widgets.Button(description = '',
                                     disabled = False,
                                     button_style = '',
                                     tooltip = 'NeuroCAAS job status')
        self.wfiles = widgets.Select(options = [],
                                    description = 'Files:')
        self.winstances = widgets.Select(options = [],
                                         description = 'Instances:')
        display(widgets.HBox([widgets.VBox([self.wstate,self.winstances]),
                                           self.wfiles]))

    def update(self):
        if self.state  in ['init','uploaded']:
            if self.fsize>0:
                if self.pbar_last != int(self.fsize/1024**2):
                    self.pbar.update(int(self.count/1024**2-self.pbar_last))
                    self.pbar_last = int(self.count/1024**2)
        
        if len(self.files):
            fs = list(filter(lambda x: len(x)>1,
                             [f.replace(self.resultsprefix,'') for f in self.files]))
            self.wfiles.options = fs
        # parse the state
        if self.state == 'init':
            self.wstate.description = 'Uploading'
            self.wstate.button_style = 'danger'
        elif self.state == 'uploaded':
            self.wstate.description = 'Submitting'
            self.wstate.button_style = 'danger'
        elif self.state == 'started':
            self.wstate.description = 'Job running'
            self.wstate.button_style = 'warning'
        elif self.state == 'finished':
            self.wstate.description = 'Job finished'
            self.wstate.button_style = 'info'
        elif self.state == 'post':
            self.wstate.description = 'Running local'
            self.wstate.button_style = 'danger'
        elif self.state == 'completed':
            self.wstate.description = 'Completed'
            self.wstate.button_style = 'success'
        if len(self.instances):
            inst = []
            for i,k in enumerate(self.instances.keys()):
                inst.append('{0} - {1}'.format(self.instances[k]['id'],self.instances[k]['dataset']))
            self.winstances.options = inst
