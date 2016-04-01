import os, sys, time, warnings
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

def prog(num,denom):
    fract = float(num)/denom
    hyphens = int(round(50*fract))
    spaces = int(round(50*(1-fract)))
    sys.stdout.write('\r%.2f%% [%s%s]' % (100*fract,'-'*hyphens,' '*spaces))
    sys.stdout.flush()     

class ProgressBar:
    """
    An animated progress bar used like:
    p = ProgressBar(1000)
    for i in range(1001):
        p.animate(i)
    """
    
    def __init__(self, iterations):
        self.iterations = iterations
        self.prog_bar = '[]'
        self.fill_char = '*'
        self.width = 40
        self.__update_amount(0)
        if have_ipython:
            self.animate = self.animate_ipython
        else:
            self.animate = self.animate_noipython

    def animate_ipython(self, iter):
        print('\r', self)
        sys.stdout.flush()
        self.update_iteration(iter + 1)

    def update_iteration(self, elapsed_iter):
        self.__update_amount((elapsed_iter / float(self.iterations)) * 100.0)
        self.prog_bar += '  %d of %s complete' % (elapsed_iter, self.iterations)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) // 2) - len(str(percent_done))
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def __str__(self):
        return str(self.prog_bar)

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
            refresh_class(obj.__class__,modules)  

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
