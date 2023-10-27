#!/bin/bash

#exec 3>&1 4>&2
#trap 'exec 2>&4 1>&3' 0 1 2 3
#exec 1>log.out 2>&1
# Everything below will go to the file 'log.out':

### Functions ###
usage() {
    echo "this is the biobakery workflow with the metaphlan4"
}


symlink_path () {
    SD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    echo $SD
}

qc() {
	echo "### QC Step"
	mkdir ./raw/qc_out
	${FASTQC} ./raw/*.f*q.gz -o ./raw/qc_out
	echo "### Finish QC"
}

kneaddata() {
	echo "### KneadData Step ###"

	${kneaddate_c} --threads ${threads} \
	--input1 ./raw/${file_name}_1.f*q.gz \
	--input2 ./raw/${file_name}_2.f*q.gz \
	--reference-db ${kneaDB} \
	--output ./kneadata/ \
	--output-prefix ${file_name} \
	--cat-final-output \
	--trimmomatic ${trimm}

	${kneaddate_c1} --input ./kneadata/ --output ./kneadata/output.log ## the stat table file

	echo "### Finish KneadData ###"
}

metaphlan() {
	echo "### MetaPhlAn4 Step"

	${metaphlan_c} ./kneadata/${file_name}.fastq \
	--input_type fastq \
	--nproc ${threads} \
	--sample_id_key ${file_name} \
	-s ./metaphlan/${file_name}_paired.sam \
	--bowtie2out ./metaphlan/${file_name}_paired.bowtie2.bz2 \
	-o ./metaphlan/${file_name}_profile.tsv

	echo "### Finish MetaPhlAn4"
}

humann() {
	echo "### HUMAnN3 Step"

	${humann_c} -i ./kneadata/${file_name}.fastq \
	--input-format fastq \
	--taxonomic-profile ./metaphlan/${file_name}_profile.tsv \
	--threads ${threads} \
	-o humann/ 

	${humann_c1} -i ./humann/${file_name}_genefamilies.tsv \
	-g uniref90_level4ec -o ./humann/${file_name}_reaction_ec.tsv

	${humann_c1} -i ./humann/${file_name}_genefamilies.tsv \
	-g uniref90_ko -o ./humann/${file_name}_reaction_ko.tsv

	${humann_c1} -i ./humann/${file_name}_genefamilies.tsv \
	-g uniref90_go -o ./humann/${file_name}_reaction_go.tsv

	echo "### Finish HUMAnN3"
}

reaction() {
	echo "### Ec number Step"

	${humann_c1} -i ./humann/${file_name}_genefamilies.tsv \
	-g uniref90_level4ec -o ./humann/${file_name}_reaction_ec.tsv

	echo "### Finish humann regroup"
}


### Initialization ###
if [ $# -eq 0  ]; then
    usage
    exit 0
else
    PROCEDURE=$1
    DIR=$(symlink_path)

    file_name=$(basename ./raw/*_1.fastq.gz _1.fastq.gz)
    echo $file_name

    threads=60
    trimm=/Trimmomatic-0.39/
    kneaddate_c=/opt/conda/bin/kneaddata
    kneaddate_c1=/opt/conda/bin/kneaddata_read_count_table
	metaphlan_c=/opt/conda/bin/metaphlan
	humann_c=/opt/conda/bin/humann
	humann_c1=/opt/conda/bin/humann_regroup_table

    kneaDB=/opt/biobakery_wf/kneaddate_db
    #humDB=/biobakery_wf_DB/

fi


### Main ###
case "${PROCEDURE}" in
info) 
    echo "The working directory is ${DIR}"
    echo "" && exit 0;;
qc)
	qc
	echo "" && exit 0;;
KNEA)
	mkdir kneadata
    kneaddata 
    echo "" && exit 0;;
META)
	mkdir metaphlan
    metaphlan 
    echo "" && exit 0;;
HUM)
	mkdir humann
    humann 
    echo "" && exit 0;;
rec)
	reaction
	echo "" && exit 0;;
ALL)
	symlink_path
	mkdir kneadata metaphlan humann

	kneaddata
	metaphlan
	humann
	echo "" && exit 0;;
test)
	metaphlan
	humann
	echo "" && exit 0;;

esac











