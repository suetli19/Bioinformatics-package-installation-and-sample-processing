#!/usr/bin/env python
__author__ = ('Michal Puncochar (michal.puncochar@unitn.it), '
              'Aitor Blanco Miguez (aitor.blancomiguez@unitn.it), '
              'Duy Tin Truong (duytin.truong@unitn.it), '
              'Francesco Asnicar (f.asnicar@unitn.it), '
              'Moreno Zolfo (moreno.zolfo@unitn.it), '
              'Francesco Beghini (francesco.beghini@unitn.it)')
__version__ = '4.0.6'
__date__ = '1 Mar 2023'



import os
import time
import pickle
import tempfile
import bz2
import pickletools
import argparse as ap
from collections import Counter
from shutil import rmtree

import pysam
import scipy.stats as sps

try:
    from .external_exec import samtools_sam_to_bam, samtools_sort_bam_v1, decompress_bz2
    from .util_fun import info, error
    from .parallelisation import execute_pool
    from .database_controller import MetaphlanDatabaseController
    from .consensus_markers import ConsensusMarker
except ImportError:
    from external_exec import samtools_sam_to_bam, samtools_sort_bam_v1, decompress_bz2
    from util_fun import info, error
    from parallelisation import execute_pool
    from database_controller import MetaphlanDatabaseController
    from consensus_markers import ConsensusMarker


class SampleToMarkers:
    """SampleToMarkers class"""

    class DEFAULTS:
        pileup_stepper = 'nofilter'
        poly_error_rate = 0.001
        min_base_coverage = 1
        min_base_quality = 30
        min_mapping_quality = 10
        poly_dominant_frq_thrsh = 0.8
        poly_pvalue_threshold = 0.05

    def decompress_from_bz2(self):
        """ Decompressed SAM.BZ2 files

        Returns:
            (list, str): tuple with the list of decompressed files and their format
        """
        results = execute_pool(
            ((SampleToMarkers.decompress_bz2_file, i, self.tmp_dir) for i in self.input), self.nprocs)
        decompressed = [r[0] for r in results]
        decompressed_format = [r[1] for r in results]
        if decompressed_format[1:] == decompressed_format[:-1]:
            if decompressed_format[0][1:].lower() == "sam":
                return decompressed, "sam"
            elif decompressed_format[0][1:].lower() == "bam":
                return decompressed, "bam"
            else:
                error("Decompressed files are not in SAM or BAM format", exit=True)
        else:
            error("Decompressed files have different formats", exit=True)

    @staticmethod
    def decompress_bz2_file(input_file, output_dir):
        """Decompress a BZ2 file and returns the decompressed file and the decompressed file format

        Args:
            input_file (str): the input file to decompress
            output_dir (str): the output directory

        Returns:
            (str, str): tuple with the decompressed file and its format
        """
        decompressed_file = decompress_bz2(input_file, output_dir)
        return decompressed_file, os.path.splitext(decompressed_file)[1]

    def convert_inputs(self):
        """Convert input sample files to sorted BAMs"""
        if self.input_format.lower() == "bz2":
            info("\tDecompressing samples...")
            self.input, self.input_format = self.decompress_from_bz2()
            info("\tDone.")
        if self.input_format.lower() == "sam":
            info("\tConverting samples to BAM format...")
            self.input = execute_pool(
                ((samtools_sam_to_bam, i, self.tmp_dir) for i in self.input), self.nprocs)
            info("\tDone.")
            info("\tSorting BAM samples...")
            self.input = execute_pool(
                ((samtools_sort_bam_v1, i, self.tmp_dir) for i in self.input), self.nprocs)
            info("\tDone.")
        elif not self.sorted:
            info("\tSorting BAM samples...")
            self.input = execute_pool(
                ((samtools_sort_bam_v1, i, self.tmp_dir) for i in self.input), self.nprocs)
            info("\tDone.")

        info('\tIndexing BAM samples...')
        execute_pool(((pysam.index, i) for i in self.input), self.nprocs)
        info('\tDone.')

    def build_consensus_markers(self, filtered):
        """Gets the markers for each sample and writes the Pickle files

        Args:
            filtered (str): string to append when filtered for clades
        """
        for i in self.input:
            info("\tProcessing sample: {}".format(i))
            results = self.get_consensuses_for_sample(i)
            self.write_results_as_pkl(filtered, os.path.splitext(
                os.path.basename(i))[0], results)
            info("\tDone.")


    def get_consensuses_for_sample(self, input_bam, stepper=DEFAULTS.pileup_stepper,
                                   error_rate=DEFAULTS.poly_error_rate,
                                   poly_pvalue_threshold=DEFAULTS.poly_pvalue_threshold):
        """Pileup on the specified BAM file

        Args:
            input_bam (str): the path to the input BAM file
            stepper (str): stepper to use in the pileup
            error_rate (float): the sequencing error rate
            poly_pvalue_threshold (float): the p-value threshold to call polymorphic position

        Returns:
            list[tuple[str, str]]: the list with the marker names and consensus sequences
        """

        info('\t\tLoading the bam file and extracting information...')
        sam_file = pysam.AlignmentFile(input_bam)

        all_markers = sam_file.references
        marker_lengths = sam_file.lengths
        marker_to_length = dict(zip(all_markers, marker_lengths))
        info('\t\tDone.')

        ACTGactg = set(list('ACTGactg'))

        info('\t\tRunning the pileup...')
        consensuses = {m: bytearray(b'-' * marker_to_length[m]) for m in all_markers}
        for base_pileup in sam_file.pileup(contig=None, stepper=stepper, min_base_quality=self.min_base_quality):
            marker = base_pileup.reference_name
            pos = base_pileup.pos
            bases = [b.upper() for b in base_pileup.get_query_sequences() if b in ACTGactg]
            base_coverage = len(bases)
            if base_coverage < self.min_base_coverage:
                continue

            base_frequencies = Counter(bases)
            max_frequency = max(base_frequencies.values())
            max_ratio = max_frequency / base_coverage
            base_consensus = base_frequencies.most_common(1)[0][0]

            if max_ratio < self.dominant_frq_threshold:
                p_value = sps.binom.cdf(max_frequency, base_coverage, 1 - error_rate)
                if p_value <= poly_pvalue_threshold:
                    base_consensus = '*'  # mask out likely polymorphic positions

            consensuses[marker][pos] = ord(base_consensus)

        info('\t\tDone.')

        consensuses = [(m, c.decode()) for m, c in consensuses.items()]  # convert bytearrays to strings
        return consensuses



    def write_results_as_pkl(self, filtered, name, results):
        """Writes the consensus sequences as a PKL file

        Args:
            filtered (str): string to append when filtered for clades
            name (str): the name of the sample
            results (list): the list with the reconstructed consensus markers
        """
        consensus = []
        for m, seq in results:
            marker = ConsensusMarker(m, seq)
            if marker.breadth >= self.breadth_threshold:
                consensus.append(
                    {"marker": marker.name, "breath": marker.breadth, "sequence": marker.sequence})
        with open(os.path.join(self.output_dir, '{}{}.pkl'.format(name, filtered)), 'wb') as markers_pkl:
            markers_pkl.write(pickletools.optimize(
                pickle.dumps(consensus, pickle.HIGHEST_PROTOCOL)))

    def parallel_filter_sam(self, input_file, filtered_markers):
        """
        Filters an input SAM file
            * filters out viral markers (VDB)
            * filters out hits with low mapQ (argument --min_mapping_quality)
            * filters out markers with not enough mapped reads (argument --min_reads_aligning)

        Args:
            input_file (str): the input SAM file
            filtered_markers (set): the list with the markers of the filtered clades, None if to use all markers

        Returns:
            str: the path to the output file
        """
        output_file = os.path.join(self.tmp_dir, input_file.split('/')[-1])
        if self.input_format.lower() == "bz2":
            ifn = bz2.open(input_file, 'rt')
            output_file = output_file.replace('.bz2', '')
        else:
            assert self.input_format.lower() == "sam"
            ifn = open(input_file, 'r')

        def filter_mapping_line(line_fields_, markers_subset):
            marker_ = line_fields_[2]
            if marker_.startswith('VDB'):
                return False
            if markers_subset is not None and marker_ not in markers_subset:
                return False
            mapq_ = int(line_fields_[4])
            if mapq_ < self.min_mapping_quality:
                return False
            return True

        marker_to_reads = Counter()
        for line in ifn:
            if line.startswith('@'):
                continue
            line_fields = line.rstrip('\n').split('\t')
            if filter_mapping_line(line_fields, filtered_markers):
                marker = line_fields[2]
                marker_to_reads[marker] += 1

        selected_markers = set((m for m, c in marker_to_reads.items() if c >= self.min_reads_aligning))

        ifn.seek(0)  # second pass of the file
        with open(output_file, 'w') as ofn:
            for line in ifn:
                line_fields = line.rstrip('\n').split('\t')
                if line.startswith('@HD'):
                    ofn.write(line)
                elif line.startswith('@'):
                    marker = line_fields[1].split(':')[1]
                    if marker in selected_markers:
                        ofn.write(line)
                else:
                    if filter_mapping_line(line_fields, selected_markers):
                        ofn.write(line)

        ifn.close()
        return output_file

    def filter_sam_files(self):
        """Filters the input SAM files with the hits against markers of specific clades"""
        filtered_markers = self.database_controller.get_filtered_markers(
            self.clades) if len(self.clades) > 0 else None
        self.input = execute_pool(
            ((self.parallel_filter_sam, i, filtered_markers) for i in self.input), self.nprocs)
        self.input_format = 'sam'
        self.sorted = False

    def run_sample2markers(self):
        """Runs the full sample2markes pipeline"""
        info("Creating temporary directory...")
        self.tmp_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        info("Done.")
        if self.input_format in ['sam', 'bz2']:
            info("Filtering SAM files...")
            self.filter_sam_files()
            info("Done.")
        info("Converting input files...")
        self.convert_inputs()
        info("Done.")
        info("Getting consensus markers from samples...")
        self.build_consensus_markers(
            filtered='_filtered' if len(self.clades) > 0 else '')
        info("Done.")
        if not self.debug:
            info("Removing temporary files...")
            rmtree(self.tmp_dir)
            info("Done.")

    def __init__(self, args):
        self.input = args.input
        self.sorted = args.sorted
        self.input_format = args.input_format
        self.output_dir = args.output_dir
        self.database_controller = MetaphlanDatabaseController(args.database)
        self.breadth_threshold = args.breadth_threshold
        self.min_reads_aligning = args.min_reads_aligning
        self.min_base_coverage = args.min_base_coverage
        self.min_base_quality = args.min_base_quality
        self.min_mapping_quality = args.min_mapping_quality
        self.dominant_frq_threshold = args.dominant_frq_threshold
        self.clades = args.clades
        self.tmp_dir = args.output_dir if args.tmp is None else args.tmp
        self.debug = args.debug
        self.nprocs = args.nprocs


def read_params():
    """ Reads and parses the command line arguments of the script

    Returns:
        namespace: The populated namespace with the command line arguments
    """
    p = ap.ArgumentParser(
        description="", formatter_class=ap.ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--input', type=str,
                   nargs='+', default=[],
                   help="The input samples as SAM or BAM files")
    p.add_argument('--sorted', action='store_true', default=False,
                   help="Whether the BAM input files are sorted")
    p.add_argument('-f', '--input_format', type=str, default="bz2",
                   help="The input samples format {bam, sam, bz2}")
    p.add_argument('-o', '--output_dir', type=str, default=None,
                   help="The output directory")
    p.add_argument('-d', '--database', type=str, default='latest',
                   help="The input MetaPhlAn " + __version__ + " database")
    p.add_argument('-b', '--breadth_threshold', type=int, default=80,
                   help="The breadth of coverage threshold for the consensus markers")
    p.add_argument('--min_reads_aligning', type=int, default=8,
                   help="The minimum number of reads to cover a marker")
    p.add_argument('--min_base_coverage', type=int, default=SampleToMarkers.DEFAULTS.min_base_coverage,
                   help="The minimum depth of coverage for a base to be considered")
    p.add_argument('--min_base_quality', type=int, default=SampleToMarkers.DEFAULTS.min_base_quality,
                   help="The minimum quality for a base to be considered. This is performed BEFORE --min_base_coverage")
    p.add_argument('--min_mapping_quality', type=int, default=SampleToMarkers.DEFAULTS.min_mapping_quality,
                   help="The minimum quality for a mapping of the read to be considered.")
    p.add_argument('--dominant_frq_threshold', type=float, default=SampleToMarkers.DEFAULTS.poly_dominant_frq_thrsh,
                   help="The cutoff for degree of 'allele dominance' for a position to be considered polymorphic")
    p.add_argument('--clades', type=str, nargs='+', default=[],
                   help="Restricts the reconstruction of the markers to the specified clades")
    p.add_argument('--tmp', type=str, default=None,
                   help="If specified, the directory where to store the temporal files")
    p.add_argument('--debug', action='store_true', default=False,
                   help="If specified, StrainPhlAn will not remove the temporal folder. "
                        "Not available with inputs in BAM format")
    p.add_argument('-n', '--nprocs', type=int, default=1,
                   help="The number of threads to execute the script")
    return p.parse_args()


def check_params(args):
    """Checks the mandatory command line arguments of the script

    Args:
        args (namespace): the arguments to check
    """
    if not args.input:
        error('-i (or --input) must be specified', exit=True)
    elif not args.input_format:
        error('-f (or --input_format) must be specified', exit=True)
    elif not args.output_dir:
        error('-o (or --output_dir) must be specified', exit=True)
    elif args.input_format.lower() not in ['bam', 'sam', 'bz2']:
        error('The input format must be SAM, BAM, or compressed in BZ2 format', exit=True)
    elif args.input_format.lower() == "bam" and len(args.clades) > 0:
        error('The --clades option cannot be used with inputs in BAM format', exit=True)
    elif not os.path.exists(args.output_dir):
        error('The directory {} does not exist'.format(
            args.output_dir), exit=True)
    elif not (args.tmp is None) and not os.path.exists(args.tmp):
        error('The directory {} does not exist'.format(args.tmp), exit=True)
    elif args.database != 'latest' and not os.path.exists(args.database):
        error('The database does not exist', exit=True)
    else:
        check_input_files(args.input, args.input_format)
    return args


def check_input_files(input_files, input_format):
    """Checks the format input sample files

    Args:
        input_files (list): list containing all the input files
        input_format (str): the format to check
    """
    for s in input_files:
        _, extension = os.path.splitext(s)
        if not os.path.exists(s):
            error('The input file \"{}\" does not exist'.format(s), exit=True)
        elif not input_format.lower() == extension[1:].lower():
            error('The the input file \"{}\" must be in \"{}\" format'.format(
                s, input_format.upper()), exit=True)


def main():
    t0 = time.time()
    args = read_params()
    info("Start samples to markers execution")
    check_params(args)
    sampletomarkers = SampleToMarkers(args)
    sampletomarkers.run_sample2markers()
    exec_time = time.time() - t0
    info("Finish samples to markers execution ({} seconds): Results are stored at \"{}\"".format(
        round(exec_time, 2), args.output_dir))


if __name__ == '__main__':
    main()
