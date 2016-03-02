import sys, time
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
