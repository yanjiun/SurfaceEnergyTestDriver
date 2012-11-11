#! /usr/bin/env python
"""
Create all of the corresponding tests for this test driver
"""

import ase.data
import os
import random
import shutil
import itertools
import tempfile
from config import KIM_REPOSITORY_DIR

KIM_TESTS_DIR = KIM_REPOSITORY_DIR + "/te"

# modify to only populate tests for elements that have defined structures in ASE
symbols = ase.data.chemical_symbols
ref_states = ase.data.reference_states
# and the cubic structures
structures = ['fcc','bcc','sc','diamond']

# folder_template = next( x for x in os.listdir(".") if x != __file__ )
folder_template = "SurfaceTest_{symbol}_{structure}__TE_{KIM}_000"

#create a temporary directory
tempdir = tempfile.mktemp()

def new_kim_number():
    # return a new kim number
    while True:
        kim_num = "{:012d}".format(random.randint(0,10**12-1))
        if all( [ kim_num not in test for test in os.listdir(KIM_TESTS_DIR) ] ):
            return kim_num


# for symbol, structure in itertools.product(symbol,structure):
for i in range(0, len(symbols)):
    symbol = symbols[i]
    if ref_states[i] is not None:
        structure = ref_states[i]['symmetry']
        if structure in structures:    
            trans_dict = { 'symbol': symbol, 'structure': structure, 'KIM': new_kim_number() }
            folder = folder_template.format(**trans_dict)
            shutil.copytree(folder_template, os.path.join(tempdir, folder))

            print folder

            #process all of the files
            for fl in os.listdir(os.path.join(tempdir,folder)):
                print fl
                # rename file
                newfl = fl.format(**trans_dict) + '~'

                shutil.move(os.path.join(tempdir,folder,fl),os.path.join(tempdir,folder,newfl))

                # replace contents
                with open(os.path.join(tempdir,folder,newfl[:-1]),'w') as newcontents:
                    contents = open(os.path.join(tempdir,folder,newfl)).read()
                    contents = contents.format(**trans_dict)
                    newcontents.write(contents)
                shutil.copymode(os.path.join(tempdir,folder,newfl),os.path.join(tempdir,folder,newfl[:-1]))

                os.remove(os.path.join(tempdir,folder,newfl))

            #now move to its home
            shutil.move(os.path.join(tempdir,folder), os.path.join(KIM_TESTS_DIR,folder))

os.rmdir(tempdir)
