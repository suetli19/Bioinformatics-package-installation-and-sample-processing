# run kneaddata on biobakery docker container

for f in `ls shared_folder/input/*_1.fq`; do 
kneaddata -t 8 --input ${f} --input ${f/_1/_2} --cat-final-output \
-db /opt/biobakery_workflows_databases/kneaddata_db_human_genome/ \
--output shared_folder/input/uq_kneaddata_out/ \
--remove-intermediate-output \
--serial \
--run-trf; done

# set kneaddata_out variable
KNEADDATA_OUT=path/to/kneaddata/output

# copy decontaminated fastq to a single folder <input>
mkdir input 
cp ${KNEADDATA_OUT}/*kneaddata.fastq input

# copy log to a single folder <log>
mkdir log
cp ${KNEADDATA_OUT}/*log log

# install MiCoP
git clone https://github.com/smangul1/MiCoP.git
cd MiCoP; ./setup.sh

cd ..

# install bwa
git clone https://github.com/lh3/bwa.git
cd bwa; make

cd ..

# install samtools
wget https://github.com/samtools/samtools/releases/download/1.14/samtools-1.14.tar.bz2
tar -xf samtools-1.14.tar.bz2
cd samtools-1.14
./configure
make

cd ..

# create output folder 
mkdir out

# run bwa sequence alignment
for f in `ls input/*fastq`; do 
~/bwa/bwa mem -t 8 -a ~/MiCoP/data/fungi-refseq.fna ${f}  > out/${f##*/}.sam
~/samtools-1.14/samtools flagstat --threads 8 out/${f##*/}.sam > out/${f##*/}.log
python3 ~/MiCoP/compute-abundances.py --fungi out/${f##*/}.sam --output out/${f##*/}_micop.txt
done
