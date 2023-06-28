# MetaPhlAn: Metagenomic Phylogenetic Analysis
[![install with bioconda](https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg?style=flat)](http://bioconda.github.io/recipes/metaphlan/README.html) [![PyPI - Downloads](https://img.shields.io/pypi/dm/metaphlan?label=MetaPhlAn%20on%20PyPi)](https://pypi.org/project/MetaPhlAn/) [![MetaPhlAn on DockerHub](https://img.shields.io/docker/pulls/biobakery/metaphlan?label=MetaPhlAn%20on%20DockerHub)](https://hub.docker.com/r/biobakery/metaphlan) [![Build MetaPhlAn package](https://github.com/biobakery/MetaPhlAn/workflows/Build%20MetaPhlAn%20package/badge.svg?branch=3.0)](https://github.com/biobakery/MetaPhlAn/actions?query=workflow%3A%22Build+MetaPhlAn+package%22)

## An updated markers database is now available!
* Addition of ~200k new genomes
* 3,580 more SGBs than the vJan21
* 2,548 genomes considered reference genomes in vJan21 were relabelled as MAGs in NCBI -> 1,550 kSGBs in vJan21 are now uSGBs in vOct22
* Removed redundant reference genomes from the vJan21 genomic database using a MASH distance threshold at 0.1%
* Local reclustering to improve SGB definitions of oversized or too-close SGBs
* Improved GGB and FGB definitions by reclustering SGB centroids from scratch
* Improved phylum assignment of SGBs with no reference genomes at FGB level using MASH distances on amino acids to find the closest kSGB

## What's new in version 4
* Adoption of the species-level genome bins system (SGBs, http://segatalab.cibio.unitn.it/data/Pasolli_et_al.html)
* New MetaPhlAn marker genes extracted identified from ~1M microbial genomes
* Ability to profile 21,978 known (kSGBs) and 4,992 unknown (uSGBs) microbial species
* Better representation of, not only the human gut microbiome but also many other animal and ecological environments
* Estimation of metagenome composed by microbes not included in the database with parameter `--unclassified_estimation`
* Compatibility with MetaPhlAn 3 databases with parameter `--mpa3`

Full list of changes [here](https://github.com/biobakery/MetaPhlAn/blob/master/CHANGELOG.md).

-------------

## Description
MetaPhlAn is a computational tool for profiling the composition of microbial communities (Bacteria, Archaea and Eukaryotes) from metagenomic shotgun sequencing data (i.e. not 16S) with species-level. With StrainPhlAn, it is possible to perform accurate strain-level microbial profiling.
MetaPhlAn 4 relies on ~5.1M unique clade-specific marker genes identified from ~1M microbial genomes (~236,600 references and 771,500 metagenomic assembled genomes) spanning 26,970 species-level genome bins (SGBs, http://segatalab.cibio.unitn.it/data/Pasolli_et_al.html), 4,992 of them taxonomically unidentified at the species level (the latest marker information file can be found [here](http://cmprod1.cibio.unitn.it/biobakery4/metaphlan_databases/mpa_vJan21_CHOCOPhlAnSGB_202103_marker_info.txt.bz2)), allowing:

* unambiguous taxonomic assignments;
* an accurate estimation of organismal relative abundance;
* SGB-level resolution for bacteria, archaea and eukaryotes;
* strain identification and tracking
* orders of magnitude speedups compared to existing methods.
* metagenomic strain-level population genomics

If you use MetaPhlAn, please cite:

[**Extending and improving metagenomic taxonomic profiling with uncharacterized species using MetaPhlAn 4.**](https://doi.org/10.1038/s41587-023-01688-w) Aitor Blanco-Miguez, Francesco Beghini, Fabio Cumbo, Lauren J. McIver, Kelsey N. Thompson, Moreno Zolfo, Paolo Manghi, Leonard Dubois, Kun D. Huang, Andrew Maltez Thomas, Gianmarco Piccinno, Elisa Piperni, Michal Punčochář, Mireia Valles-Colomer, Adrian Tett, Francesca Giordano, Richard Davies, Jonathan Wolf, Sarah E. Berry, Tim D. Spector, Eric A. Franzosa, Edoardo Pasolli, Francesco Asnicar, Curtis Huttenhower, Nicola Segata. Nature Biotechnology (2023)

If you use StrainPhlAn, please cite the MetaPhlAn paper and the following StrainPhlAn paper:

[**Microbial strain-level population structure and genetic diversity from metagenomes.**](http://genome.cshlp.org/content/27/4/626.full.pdf) *Duy Tin Truong, Adrian Tett, Edoardo Pasolli, Curtis Huttenhower, & Nicola Segata*. Genome Research 27:626-638 (2017)

-------------

## Installation
The best way to install MetaPhlAn is through conda via the Bioconda channel. If you have not configured you Anaconda installation in order to fetch packages from Bioconda, **please follow [these steps](https://bioconda.github.io/user/install.html#set-up-channels) in order to setup the channels.**

You can install MetaPhlAn by running

```
$ conda install -c bioconda metaphlan
```

For installing it from the source code and for further installation instructions, please see the Wiki at the [Installation](https://github.com/biobakery/MetaPhlAn/wiki/MetaPhlAn-4#installation) paragraph.

-------------

## MetaPhlAn and StrainPhlAn tutorials and resources

In addition to the information on this page, you can refer to the following additional resources.

* The [MetaPhlAn documentation](https://github.com/biobakery/MetaPhlAn/wiki/MetaPhlAn-4).

* The [StrainPhlAn documentation](https://github.com/biobakery/MetaPhlAn/wiki/StrainPhlAn-4).

* Related tools including [PanPhlAn](https://github.com/segatalab/panphlan) (and its [tutorial](https://github.com/segatalab/panphlan/wiki/Home)), [GraPhlAn](https://github.com/segatalab/graphlan) (and it [tutorial](https://github.com/biobakery/biobakery/wiki/graphlan)), [PhyloPhlAn 3](https://github.com/biobakery/phylophlan) (and its [tutorial](https://github.com/biobakery/biobakery/wiki/phylophlan)), [HUMAnN](https://github.com/biobakery/humann/) (and its [tutorial](https://github.com/biobakery/biobakery/wiki/humann2)).

* The related [bioBakery workflows](https://github.com/biobakery/biobakery/wiki/biobakery_workflows)
