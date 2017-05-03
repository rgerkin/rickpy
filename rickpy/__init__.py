import os, sys, time, warnings, shutil

try:
    from IPython.display import clear_output,Image,HTML
    import nbformat
    have_ipython = True
except ImportError:
    have_ipython = False

THEN = None


def tic():
    global THEN
    THEN = datetime.now()


def toc(activity='Something'):
    now = datetime.now()
    delta = now - THEN
    seconds = delta.days*24*3600 + delta.seconds + delta.microseconds/1e6
    print('%s took %.3g seconds' % (activity,seconds))


class ProgressBar:
    """
    An animated progress bar used like:
    n = 1000
    p = ProgressBar(n)
    for i in range(n):
        p.animate(i)
        # Or using optional message:
        # p.animate(i,"{k} out of {n} complete")
        time.sleep(1) # Replaced by your code
    p.animate(n)
    """
    
    def __init__(self, n, progress='{k} out of {n} complete', status=''):
        self.n = n
        self.progress = progress
        self.status = status
        self.char = '-'
        self.width = 50
        self.last_length = 0
        self._update(0, '')

    def animate(self, k, status=None):
        if status is None:
            status = self.status
        sys.stdout.write('\r%s' % (' '*self.last_length))
        self._update(k, status)
        sys.stdout.write('\r%s' % self.text)
        sys.stdout.flush()
        
    def _update(self, k, status):
        percent = int(k*100/self.n)
        n_chars = int(round((percent / 100.0) * (self.width-2)))
        self.text = "[%s%s]" % (self.char*n_chars,' '*(self.width-2-n_chars))
        pct = ('%d%%' % percent)
        self.text = self.text[:int(self.width/2)-1] + pct + self.text[int(self.width/2)-1+len(pct):]
        self.text += ' '+self.progress.format(k=k,n=self.n)
        if status:
            self.text += ' (%s)' % status
        self.last_length = len(self.text)

ENCRYPTION_PREFIX = '%%%%%'
ENCRYPTION_SHIFT = 37
    

# An ovaltine-esque code.  
def encrypt(x,n=ENCRYPTION_SHIFT):
    return ENCRYPTION_PREFIX+base64.b64encode(''.join([chr((ord(i)+n) % 256) for i in x]))


# An ovaltine-esque code.  
def decrypt(x,n=ENCRYPTION_SHIFT):
    return ''.join([chr((ord(i)-n+256) % 256) for i in base64.b64decode(x[len(ENCRYPTION_PREFIX):])])
    

def is_encrypted(x):
    return x[0:len(ENCRYPTION_PREFIX)] == ENCRYPTION_PREFIX


def get_outputs(nb_name, n_cell):
    """Get output cells from an IPython notebook on disk"""

    with open('%s.ipynb' % nb_name,'r') as f:
        nb = nbformat.read(f, as_version=4)
    outputs = []
    result = None
    for c in nb.cells:
        if c['cell_type']=='code' and c['execution_count']==n_cell:
            outputs += c['outputs']
    return outputs


def get_fig(nb_name, n_cell, n_output=0):
    """Get output figure from an IPython notebook on disk"""

    outputs = get_outputs(nb_name,n_cell)
    base64 = outputs[n_output]['data']['image/png']
    return Image(data=base64, format='png')


def get_table(nb_name, n_cell, n_output=0):
    """Get output table (or any html) from an IPython notebook on disk"""

    outputs = get_outputs(nb_name,n_cell)
    html = outputs[n_output]['data']['text/html']
    return HTML(html)


def refresh_class(cls,modules):
    """Updates one class recursively so that it and all of its bases classes 
    match the current version of the class."""

    bases = cls.__bases__
    if bases is (object,):
        return 0
    bases = list(bases)
    changed = False
    for i,base in enumerate(bases):
        if base is object:
            continue
        mod = base.__module__
        if (modules is None) or any([x in mod for x in modules]):
            try:
                base_name = str(base)[8:-2]
                module_name = base_name
                while True:
                    try:
                        module = __import__(module_name)
                    except ImportError as e:
                        if '.' in module_name:
                            module_name = '.'.join(module_name.split('.')[:-1])
                        else:
                            warnings.warn(str(e))
                            break
                    else:
                        skip_list = ['numpy'] # Modules to never try to refresh.  
                        skip_flag = False
                        for skip in skip_list:
                            if skip in base_name:  
                                skip_flag = True
                        if skip_flag:
                            break
                        base_name = base_name.split('.')
                        full_class = module
                        for j,part in enumerate(base_name):
                            if j>0:
                                full_class = getattr(full_class,part)
                        bases[i] = full_class
                        changed = True
                        break
            except Exception as e:
                warnings.warn(str(e))
                #raise(e)
        refresh_class(base,modules)
    if changed:
        try:
            cls.__bases__ = tuple(bases)
        except TypeError as e:
            raise(e)
            

def refresh_objects(objects,modules=None):
    """Updates objects recursively so that they and all of their members
    have classes that match the current version of those classes.
    Use with locals() to update everything in a notebook."""
    
    for name,obj in objects.copy().items():
        if type(obj) is list:
            for obj_ in obj:
                refresh_class(obj_.__class__,modules)
        elif type(obj) is dict:
            for obj_ in obj.values():
                refresh_class(obj_.__class__,modules)
        else:
            refresh_class(obj.__class__,modules) # Refresh the class itself
            #try:
            #    obj.__class__ = eval(str(obj.__class__)[8:-2]) # Refresh the object
            #except TypeError:
            #    pass


def use_dev_packages(dev_packages):
    """Prepends items in dev_packages to sys.path, and assumes there are in 
    the user's HOME/Dropbox/dev directory. 
    Format for dev_packages items is repo/package.
    """

    HOME = os.path.expanduser('~')
    sp = os.path.join(HOME,'Dropbox/python3/lib/python3.4/site-packages')
    if os.path.exists(sp) and sp not in sys.path:
        sys.path.append(sp)  
    for i,package in enumerate(dev_packages):
        if package.split('/')[-1] not in sys.path[len(dev_packages)-i]:
            sys.path.insert(1,os.path.join(HOME,'Dropbox/dev/',package))   
