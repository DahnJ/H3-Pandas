##!/bin/bash -e
# Based on script from Qiusheng Wu

# Variables
pkg='h3pandas'
array=( 3.8 3.9 3.10 3.11)

# Constants
MINICONDA=$HOME/miniconda3

#echo "Building conda package ..."
cd $HOME
grayskull pypi $pkg

# update meta.yaml
echo "Updating meta.yaml ..."
sed -i 's/^\(\s\+- h3\)$/\1-py/g' $pkg/meta.yaml
sed -i 's/^\(\s\+-\) your-github-id-here/\1 DahnJ/g' $pkg/meta.yaml

# building conda packages
for i in "${array[@]}"
do
    echo "Building for Python $i"
	conda-build --python $i $pkg
done

# upload packages to conda
find $MINICONDA/conda-bld/ -name *.tar.bz2 | while read file
do
    echo $file
    anaconda upload $file
done
echo "Building conda package done!"

rm $HOME/h3pandas -r
conda build purge-all
