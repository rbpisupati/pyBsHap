"""
    pyBsHap
    ~~~~~~~~~~~~~
    The main module for running pyBsHap
    :copyright: year by my name, see AUTHORS for more details
    :license: license_name, see LICENSE for more details
"""
import os
import os.path
import argparse
import sys
from bshap.core import prebshap
from bshap.core import bsseq
from bshap.core import bamEdit
from bshap.core import meth5py
from bshap.core import plotting
import logging, logging.config

__version__ = '1.1.0'
__updated__ = "17.01.2018"
__date__ = "10.12.2016"

def setLog(logDebug):
  log = logging.getLogger()
  if logDebug:
    numeric_level = getattr(logging, "DEBUG", None)
  else:
    numeric_level = getattr(logging, "ERROR", None)
  log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  lch = logging.StreamHandler()
  lch.setLevel(numeric_level)
  lch.setFormatter(log_format)
  log.setLevel(numeric_level)
  log.addHandler(lch)

def die(msg):
  sys.stderr.write('Error: ' + msg + '\n')
  sys.exit(1)

def get_options(program_license,program_version_message):
  inOptions = argparse.ArgumentParser(description=program_license)
  inOptions.add_argument('-V', '--version', action='version', version=program_version_message)
  subparsers = inOptions.add_subparsers(title='subcommands',description='Choose a command to run',help='Following commands are supported')

  methbam = subparsers.add_parser('getmeth', help="Get methylation on each read from the aligned bam files")
  methbam.add_argument("-i", "--input_bam", dest="inFile", help="aligned BAM file for bs-seq reads")
  methbam.add_argument("-r", "--fasta-file", dest="fastaFile", help="Reference fasta file, TAIR10 genome")
  methbam.add_argument("-s", "--specificRegion", dest="reqRegion", help="region to be checked, Ex. Chr1,1,100 --- an aln file is generated given this", default = '0,0,0')
  methbam.add_argument("-o", "--output", dest="outFile", help="Output file with the methylation across windows")
  methbam.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  methbam.set_defaults(func=bshap_methbam)

  mhlparser = subparsers.add_parser('getmhl', help="Get methylation haplotype load from the read data from the aligned bam files")
  mhlparser.add_argument("-i", "--input_bam", dest="inFile", help="aligned BAM file for bs-seq reads")
  mhlparser.add_argument("-r", "--fasta-file", dest="fastaFile", help="Reference fasta file, TAIR10 genome")
  mhlparser.add_argument("-d", "--in_hdf5", dest="inhdf5", help="hdf5 file generated using meth5py")
  mhlparser.add_argument("-w", "--window_size", dest="window_size", help="window size", type = int, default=80)
  mhlparser.add_argument("-x", "--specificRegion", dest="reqRegion", help="region to be checked, Ex. Chr1,1,100 --- an aln file is generated given this", default = '0,0,0')
  mhlparser.add_argument("-s", "--strand", dest="strand", help="strand for the reads to get the MHL, maybe later I would print for the both", type = str, default='0')
  mhlparser.add_argument("-o", "--output", dest="outFile", help="Output file", default="STDOUT")
  mhlparser.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  mhlparser.set_defaults(func=bshap_mhlcalc)

  permeth_parser = subparsers.add_parser('methylation_percentage', help="Get methylation percentage on the given bin position.")
  permeth_parser.add_argument("-i", "--input_file", dest="inFile", help="Input methylation HDF5 file generated from allc files", required=True)
  permeth_parser.add_argument("-a", "--allc_path", dest="allc_path", help="Possible options: 1) Bash path, allc files from this path with sample ID are used. 2) hdf5, then the input file is a hdf5 formatted file. 3) bed, the input file is a bed file (also gzipped).", required=True)
  permeth_parser.add_argument("-b", "--required_region", dest="required_region", help="Bed region to calculate the methylation averages. ex. Chr1,1,100", default = '0,0,0')
  permeth_parser.add_argument("-w", "--window_size", dest="window_size", help="window size to get the methylation averages", type = int, default=200)
  permeth_parser.add_argument("-x", "--overlap", dest="overlap", type=int, help="overlap in the windows generated", default=0)
  permeth_parser.add_argument("-c", "--methylation_averaging_method", dest="category", help="different methylation average methods, 1 -- weighted average, 2 -- methylation calls, 3 -- average methylation per position", default = 1, type = int)
  permeth_parser.add_argument("-o", "--output", dest="outFile", help="output file.")
  permeth_parser.add_argument("-p", "--bedtools_path", dest="bedtoolsPath", help="path to bedtools used for genome wide averages")
  permeth_parser.add_argument("-t", "--context", dest="context", help="required context to get the average, ex. C[ATC]G, C[ATC][ATC], CG, CTA, etc")
  permeth_parser.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  permeth_parser.set_defaults(func=bsseq_meth_average)

  modifybam = subparsers.add_parser('modifymdtag', help="Modify MD tag on BAM files to get default coloring in jbrowse")
  modifybam.add_argument("-i", "--input_bam", dest="inFile", help="aligned BAM file for bs-seq reads")
  modifybam.add_argument("-r", "--fasta-file", dest="fastaFile", help="Reference fasta file, TAIR10 genome")
  modifybam.add_argument("-s", "--specificRegion", dest="reqRegion", help="region to be checked, Ex. Chr1,1,100 --- an aln file is generated given this", default = '0,0,0')
  modifybam.add_argument("-o", "--output", dest="outFile", help="Output file with the methylation across windows")
  modifybam.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  modifybam.set_defaults(func=bshap_modifybam)

  callmc_parser = subparsers.add_parser('callmc', help="Call mc using methylpy from fastq file")
  callmc_parser.add_argument("-i", "--input_file", dest="inFile", help="Input fastq file for methylpy")
  callmc_parser.add_argument("-s", "--sample_id", dest="sample_id", help="unique sample ID for allc Files")
  callmc_parser.add_argument("-r", "--ref_fol", dest="ref_fol", help="methylpy reference folder for indices and refid", default="/home/GMI/rahul.pisupati/TAiR10_ARABIDOPSIS/03.methylpy.indices/tair10")
  callmc_parser.add_argument("-f", "--ref_fasta", dest="ref_fasta", help="reference fasta file", default="/home/GMI/rahul.pisupati/TAiR10_ARABIDOPSIS/TAIR10_wholeGenome.fasta")
  callmc_parser.add_argument("-n", "--nt", dest="nt", help="number of threads", default=2,type=int)
  callmc_parser.add_argument("-c", "--unMethylatedControl", dest="unMeth", help="unmethylated control", default="ChrC:")
  callmc_parser.add_argument("-m", "--mem", dest="memory", help="memory for sorting", default="2G")
  callmc_parser.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  callmc_parser.set_defaults(func=callmcs_onesample)

  dmr_parser = subparsers.add_parser('dmrfind', help="Identify DMR using methylpy")
  dmr_parser.add_argument("-s", "--sample_ids", dest="sample_ids", help="sample ids, comma seperated")
  dmr_parser.add_argument("-r", "--sample_categories", dest="sample_cat", help="sample categories indicating replicates, comma separated", default="0")
  dmr_parser.add_argument("-p", "--path", dest="path_to_allc", help="path to allc files")
  dmr_parser.add_argument("-c", "--context", dest="mc_type", help="methylation context, context separated")
  dmr_parser.add_argument("-n", "--nt", dest="nt", help="number of threads", default=2,type=int)
  dmr_parser.add_argument("-o", "--outDMR", dest="outDMR", help="output file for DMR")
  dmr_parser.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  dmr_parser.set_defaults(func=dmrfind)

  lowfreq_parser = subparsers.add_parser('callLowFreq', help="Get lowfreq positions from allc files")
  lowfreq_parser.add_argument("-s", "--sample_id", dest="sample_id", help="unique sample ID for allc Files")
  lowfreq_parser.add_argument("-p", "--path", dest="path_to_allc", help="path to allc files")
  lowfreq_parser.add_argument("-c", "--unMethylatedControl", dest="unMeth", help="unmethylated control", default="ChrC")
  lowfreq_parser.add_argument("-e", "--pvalue_thres", dest="pvalue_thres", help="threshold for p-value to call low-freq site", default=0.05)
  lowfreq_parser.add_argument("-o", "--outFile", dest="outFile", help="output h5py file")
  lowfreq_parser.add_argument("-v", "--verbose", action="store_true", dest="logDebug", default=False, help="Show verbose debugging output")
  lowfreq_parser.set_defaults(func=lowfindfind)

  return inOptions

def checkARGs(args):
    if not args['inFile']:
        die("input file not specified")
    if not args['fastaFile']:
        die("fasta file not specified")
    if not args['outFile']:
        die("output file not specified")
    if not os.path.isfile(args['fastaFile']):
        die("fasta file does not exist: " + args['fastaFile'])
    if not os.path.isfile(args['inFile']):
        die("input file does not exist: " + args['inFile'])

def bshap_methbam(args):
    checkARGs(args)
    if os.path.isfile(args['reqRegion']):
        prebshap.getMethsRegions(args['inFile'], args['fastaFile'], args['outFile'], args['reqRegion'])
    else:
        prebshap.getMethGenome(args['inFile'], args['fastaFile'], args['outFile'], args['reqRegion'])

def bshap_mhlcalc(args):
    checkARGs(args)
    prebshap.potato_mhl_calc(args)

def bshap_modifybam(args):
    checkARGs(args)
    bamEdit.writeBam(args['inFile'], args['fastaFile'], args['outFile'], args['reqRegion'])

def callMPsfromVCF(args):
  if not args['inFile']:
    die("input file not specified")
  if not args['outFile']:
    die("output file not specified")
  if not os.path.isfile(args['inFile']):
    die("input file does not exist: " + args['inFile'])
  bsseq.getMPsfromVCF(args)

def callmcs_onesample(args):
    if not args['inFile']:
        die("input file not specified")
    if not os.path.isfile(args['inFile']):
        die("input file does not exist: " + args['inFile'])
    bsseq.methylpy_callmcs(args)

def dmrfind(args):
    bsseq.methylpy_dmrfind(args)

def lowfindfind(args):
    bsseq.getLowFreqSites(args)

def bsseq_meth_average(args):
    meth5py.potatoskin_methylation_averages(args)


def main():
  ''' Command line options '''
  program_version = "v%s" % __version__
  program_build_date = str(__updated__)
  program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
  program_shortdesc = "The main module for pyBsHap"
  program_license = '''%s
  Created by Rahul Pisupati on %s.
  Copyright 2016 Gregor Mendel Institute. All rights reserved.

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.
USAGE
''' % (program_shortdesc, str(__date__))

  parser = get_options(program_license,program_version_message)
  args = vars(parser.parse_args())
  setLog(args['logDebug'])
  if 'func' not in args:
    parser.print_help()
    return 0
  try:
    args['func'](args)
    return 0
  except KeyboardInterrupt:
    return 0
  except Exception as e:
    logging.exception(e)
    return 2

if __name__=='__main__':
  sys.exit(main())
