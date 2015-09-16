try:
    import cPickle as pickle
except:
    import pickle

import pandas as pd

def pickle_save(d, fn):
    '''Utility to save pickle files'''
    with open(fn, 'wb') as f:
        pickle.dump(d, f, protocol=2)


def pickle_load(fn):
    '''Utility to load pickle files'''
    with open(fn, 'rb') as f:
        x = pickle.load(f)
        return x

def concatDfFilelist(slicedFiles, deslicedData=None):
    '''Concats a list of files, appending onto a new data frame
    if it doesn't exist and then returning. If the df already exists,
    editing is in place and the return is redundant
    '''
    for slicedFile in slicedFiles:
        tmpdf = pickle_load(slicedFile)
        try:
            print('Concating file %s...' % slicedFile)
            deslicedData = pd.concat([deslicedData, tmpdf], axis=0, ignore_index=True)
        except NameError:
            print('First iteration')
            deslicedData = tmpdf
        print('Rows: %s' % len(deslicedData))
    return deslicedData
