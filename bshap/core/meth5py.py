# Main module for bisulfite analysis
# Summary statistics

import h5py as h5
import numpy as np

#def load_allc_methylation_files(allc_path,bin_bed=''):

def load_hdf5_methylation_file(hdf5_file, bin_bed=''):
    return HDF5MethTable(hdf5_file, bin_bed)

# Try to make it as a class, learned from PyGWAS
class HDF5MethTable(object):

    def __init__(self,hdf5_file, bin_bed=''):
        self.h5file = h5.File(hdf5_file,'r')
        self.filter_pos_ix = self.get_filter_inds(bin_bed)
        self.chr = self.get_chrs()
        self.positions = self.get_positions()

    def close_h5file(self):
        if self.h5file is not None:
            self.h5file.close()

    def get_filter_inds(self, bin_bed):
        # bin_bed = ['Chr1', 0, 100]
        if bin_bed == '':
            return(None)
        x_chrs = np.core.defchararray.decode(np.array(self.h5file['chr']), encoding='ascii')
        x_pos = np.array(self.h5file['pos'])
        req_chr_inds = np.where(x_chrs == bin_bed[0])[0]
        req_inds = req_chr_inds[np.where((x_pos[req_chr_inds] < bin_bed[2]) & (x_pos[req_chr_inds] > bin_bed[1]))[0]]
        return(req_inds)

    def get_chrs(self):
        if self.filter_pos_ix is not None:
            return(np.core.defchararray.decode(np.array(self.h5file['chr'])[self.filter_pos_ix], encoding='ascii'))
        return(np.core.defchararray.decode(np.array(self.h5file['chr']), encoding='ascii'))

    def get_positions(self):
        if self.filter_pos_ix is not None:
            return(np.array(self.h5file['pos'])[self.filter_pos_ix])
        return(np.array(self.h5file['pos']))

    def get_methylated(self):
        if self.filter_pos_ix is not None:
            self.methylated = np.array(self.h5file['methylated'])[self.filter_pos_ix]
        else:
            self.methylated = np.array(self.h5file['methylated'])

    def get_strand(self):
        if self.filter_pos_ix is not None:
            self.strand = np.array(self.h5file['strand'])[self.filter_pos_ix]
        else:
            self.strand = np.array(self.h5file['strand'])

    def get_mc_class(self):
        if self.filter_pos_ix is not None:
            self.mc_class = np.array(self.h5file['mc_class'])[self.filter_pos_ix]
        else:
            self.mc_class = np.array(self.h5file['mc_class'])

    def get_mc_count(self):
        if self.filter_pos_ix is not None:
            self.mc_count = np.array(self.h5file['mc_count'])[self.filter_pos_ix]
        else:
            self.mc_count = np.array(self.h5file['mc_count'])

    def get_lowfreq(self):
        if self.filter_pos_ix is not None:
            self.lowfreq = np.array(self.h5file['lowfreq'])[self.filter_pos_ix]
        else:
            self.lowfreq = np.array(self.h5file['lowfreq'])

    def get_mc_total(self):
        if self.filter_pos_ix is not None:
            self.mc_total = np.array(self.h5file['total'])[self.filter_pos_ix]
        else:
            self.mc_total = np.array(self.h5file['total'])

def MethylationSummaryStats(meths, category):
    # meths is already filtered for bin_bed positions
    try:
        bin_len = len(meths.__dict__['mc_total'])
    except KeyError:
        meths.get_mc_total()
        meths.get_mc_count()
    if category == 1:   # weighted mean
        return np.divide(np.sum(meths.mc_count), np.sum(meths.mc_total))
    elif category == 2: # get only methylated positions
        try:
            meths_len = np.sum(meths.__dict__['methylated'])
        except KeyError:
            meths.get_methylated()
            meths_len = np.sum(meths.__dict__['methylated'])
        return float(meths_len)/bin_len
    elif category = 3: ## absolute means
        return(np.mean(np.divide(meths.mc_count, meths.mc_total)))

def get_Methlation_GenomicRegion(hdf5_file, bin_bed, category = 1):
    meths = load_hdf5_methylation_file(hdf5_file, bin_bed)
    return(MethylationSummaryStats(meths, category))
