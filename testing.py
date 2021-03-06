#!/usr/bin/python
import matplotlib
matplotlib.use('Agg')
import ase
from ase.structure import bulk
import numpy as np
from chooseSurfaces import *
from surface import *
from kimcalculator import *
from analysis import *
import simplejson
import pickle
import scipy.optimize as opt
import sys
import signal
import time

symbol = raw_input()
lattice = raw_input()
model = raw_input()

TIME_CUTOFF = 300
# in seconds 

def sweepSurfaces(calc):

    surfaceEnergyDict = {}
    energies=[]
    skipped_indices=[]
    indices_calculated=[]
    file = open('IndexList.pkl','r')
    list_of_indices = pickle.load(file)
    file.close()
    # list of indices for testing
    list_of_indices = [[1,0,0],[1,1,1],[1,2,1],[1,1,0],[1,8,9]]
    latticeconstant = findLatticeConstant(calc)
    atoms = bulk(symbol,lattice,a=latticeconstant)
    atoms.set_calculator(calc)
    unit_e_bulk = atoms.get_potential_energy()/atoms.get_number_of_atoms()
    
    # testing time for the calculation of 1 surface
    # start an alarm
    signal.signal(signal.SIGALRM, handler1)
    signal.alarm(TIME_CUTOFF)
    start_time = time.time()
    if lattice == 'fcc':
        miller = [1,1,1]
    elif lattice == 'bcc':
        miller = [1,0,0]
    else:
        miller = [1,0,0]
    #E_unrelaxed, E_relaxed = getSurfaceEnergy(miller, calc, unit_e_bulk, latticeconstant)
    signal.alarm(0)
    end_time = time.time()
    calcTime = end_time - start_time

    counter = 0
    signal.signal(signal.SIGALRM, handler2)
    for miller in list_of_indices:
        signal.alarm(TIME_CUTOFF)
        try:
            print miller
            E_unrelaxed, E_relaxed = getSurfaceEnergy(miller, calc, unit_e_bulk, latticeconstant)
            surfaceEnergyDict['Surface Energy ' +str(miller)] = E_relaxed
            energies.append(E_relaxed) 
            indices_calculated.append(miller)
        except TimeoutException:
            skipped_indices.append(miller)
            print "surface took too long, skipping", miller
        except:
            raise
        signal.alarm(0)
    return indices_calculated, np.array(energies), surfaceEnergyDict, calcTime 

def getSurfaceEnergy(miller, calc, unit_e_bulk, latticeconstant):
    
    surf = makeSurface(symbol,lattice,miller,size = (3, 3, 10),lattice_const=latticeconstant)
    e_unrelaxed, e_relaxed = surface_energy(surf, calc)
    e_bulk = unit_e_bulk*surf.get_number_of_atoms()
    surface_vector = np.cross(surf.cell[0],surf.cell[1])
    surface_area = np.sqrt(np.dot(surface_vector,surface_vector))
    E_unrelaxed = (e_unrelaxed-e_bulk)/(2*surface_area)
    E_relaxed = (e_relaxed-e_bulk)/(2*surface_area)
    
    return E_unrelaxed, E_relaxed

def fitBrokenBond(indices, energies, n=3, p0=[0.1,0.1,0.01,0.0],correction=1):

    indices = np.array(indices)
    
    bfparams, cov_x, cost, range, max_error = fitSurfaceEnergies(indices,energies,n=n,p0=p0,correction=correction)     

    return bfparams, range, max_error

def fitSubSetBrokenBond(sample_indices,indices,energies,n=3,p0=[0.1,0.1,0.01,0.0],correction=1):
    
    expandedIndices, expandedEnergies = expandList(indices, energies)

    sample_energies=[]

    for ind in sample_indices:
        curr_index = expandedIndices.index(ind)
        sample_energies.append(expandedEnergies[curr_index])
 
    bfparams, range, max_error = fitBrokenBond(sample_indices, sample_energies, n=n, p0 = p0,correction=correction)

    return bfparams, range, max_error

def plotBrokenBondFit(indices,energies,bfparams,correction=1):
   
    # modify to include three cyrstallographic zone cutoffs
    plotindices, plotenergies = expandList(indices,energies)
    plotSubSet(plotindices,plotenergies,[1,-1,0],[1,1,0],bfparams,correction=correction)
    pylab.savefig('BrokenBondFit1-10.png')
    plotSubSet(plotindices,plotenergies,[1,-1,2],[1,1,0],bfparams,correction=correction)
    pylab.savefig('BrokenBondFit1-12.png')
    plotSubSet(plotindices,plotenergies,[1,1,-1],[0,1,1],bfparams,correction=correction)
    pylab.savefig('BrokenBondFit11-1.png')


def findLatticeConstant(calc):
    """
    temporary copy of Alex's LatticeConstantCubicEnergy Test
    in the future we want to look up the result of this as input to the test
    """
    
    XTOL = 1e-8    

    nn_dist_lookup = {"sc": 1.,
        "fcc" : 1./np.sqrt(2),
        "bcc": np.sqrt(3)/2.,
        "diamond": np.sqrt(3)/4. }

    nn_dist = nn_dist_lookup[lattice]
    
    atoms = bulk(symbol,lattice,a=100)
    atoms.set_calculator(calc)
    cutoff = KIM_API_get_data_double(calc.pkim,"cutoff")[0]

    min_a = (cutoff/30.0)/nn_dist
    max_a = cutoff/nn_dist

    aopt, eopt, ier, funccalls = opt.fminbound(calcEnergy, min_a, max_a, args= (calc,),full_output = True, xtol=XTOL)

    #results = opt.fmin(calcEnergy, cutoff/2.0, args=(calc,))[0]
    
    hit_bound = False
    if np.allclose(aopt,min_a,atol=2*XTOL):
        hit_bound = True    
    elif np.allclose(aopt,max_a,atol=2*XTOL):
        hit_bound = True

    if hit_bound:
        raise Exception("Lattice constant computation hit bounds")    

    return aopt

def calcEnergy(a, calc):
    
    atoms = bulk(symbol,lattice,a=a)
    atoms.set_calculator(calc)
    try:
        energy = atoms.get_potential_energy()
    except:
        energy = 1e10
    
    return energy

def handler1(signum,frame):
    raise Exception("first calculation took too long, aborting model-test pair")

def handler2(signum,frame):
    raise TimeoutException()

class TimeoutException(Exception):
    pass


calc = KIMCalculator(model)
print "calculator established"
indices, energies, surfaceEnergyDict, calcTime  = sweepSurfaces(calc)
print "surfaces swept"
if len(indices)>=4:
    bfparams, range_error, max_error = fitBrokenBond(indices, energies)
    plotBrokenBondFit(indices,energies,bfparams)

    # fit the minimum subset and see how well it does
    samplelist = [[1,1,1],[1,0,0],[1,1,2],[1,0,1]] 
    subbfparams, subrange, submax_error = fitSubSetBrokenBond(samplelist,indices, energies)
else:
    bfparams = None
    range_error = None
    max_error = None
    subbfparams = None
    subrange = None
    submax_error = None

# dump all the stuff we calculated into one large dictionary
if bfparams!=None:
    resultsFirstHalf = {'BrokenBondParameter(110)': bfparams[0], \
        'BrokenBondParameter(100)':bfparams[1], \
        'BrokenBondParameter(112)':bfparams[2], \
        'CorrectionParameter':bfparams[3],
        'Error/Range(%)':range_error,
        'Max Residual(%)':max_error,
        'Subset prediction Quality': submax_error, 
        "BrokenBondFitPlot1-10": "@FILE[BrokenBondFit1-10.png]",
        "BrokenBondFitPlot1-12": "@FILE[BrokenBondFit1-12.png]",
        "BrokenBondFitPlot11-1": "@FILE[BrokenBondFit11-1.png]",
        "calculationTimeForTestSurface" : calcTime\
        }
else:
    resultsFirstHalf = {"calculationTimeForTestSurface":calcTime,\
                        "message from test":"not enough surface energy results for fit"}

results = dict(resultsFirstHalf.items()+surfaceEnergyDict.items())
print simplejson.dumps(results)

sys.exit(0)
