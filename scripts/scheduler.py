__author__ = 'gsanroma'

import os
import subprocess
from time import sleep
from sys import platform

#
# # Class sbatch launcher
#

class Launcher(object):

    def __init__(self, cmd):

        self.name = 'script.sh'
        self.folder = './'
        self.queue = 'short'
        self.cmd = cmd
        self.omp_num_threads = 0
        self.run_in_gpu = False

        if platform == 'darwin':
            self.is_hpc = False
        else:
            self.is_hpc = True

    def run(self):

        script_file = os.path.join(self.folder, self.name + '.sh')
        f = open(script_file,'w')

        if self.is_hpc:

            outfile = "{}.out".format(os.path.join(self.folder,self.name))
            errfile = "{}.err".format(os.path.join(self.folder,self.name))
            try:
                os.remove(outfile)
                os.remove(errfile)
            except:
                pass

            executable = "sbatch"
            f.write("#!/bin/bash\n")
            if self.name[0].isdigit():
                scriptname = 's' + self.name
            else:
                scriptname = self.name
                
            f.write("#SBATCH --job-name {}\n".format(scriptname))
            f.write("#SBATCH --workdir=\n")
            f.write("#SBATCH -p {}\n".format(self.queue))
            f.write("#SBATCH -o {}\n".format(outfile))
            f.write("#SBATCH -e {}\n".format(errfile))
            f.write("#SBATCH --mem {}\n".format(512))
            if self.run_in_gpu:
                f.write("#SBATCH -l gpu=1\n")
            if self.omp_num_threads > 0:
                f.write("#SBATCH -n ompi* %d\n" % self.omp_num_threads)
                f.write("#SBATCH --export=OMP_NUM_THREADS=%d\n" % self.omp_num_threads)
            f.write("#SBATCH --export=ANTSPATH=%s\n" % os.environ['ANTSPATH'])
            f.write("#SBATCH --export=ANTSSCRIPTS=%s\n" % os.environ['ANTSSCRIPTS'])


        else:
            executable = "bash"

        if self.run_in_gpu:
            f.write('module load CUDA/8.0.61\n')
            f.write('THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 ' + self.cmd)
        else:
            f.write(self.cmd)
        f.close()

        # print "Launching {}".format(self.name)

        if self.is_hpc:
            ex_out = subprocess.check_output([executable,script_file])
            return ex_out.split()[2]
        else:
            subprocess.call([executable,script_file])
            return



def check_file_repeat(filename,n_repeats=5,wait_seconds=5):

    i = 0
    f = None
    while i < n_repeats:
        try:
            f = open(filename,'r')
        except:
            i += 1
            print("Failed attempt at reading {}".format(filename))
            sleep(wait_seconds)
            print("Retrying...")
            continue
        break
    assert f, "Cannot open qsub output file: {}".format(filename)
