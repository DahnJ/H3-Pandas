##!/bin/bash -e
# Based on script from Qiusheng Wu

# Variables
pkg='h3pandas'
# array=( 3.7 3.8 3.9 ) TODO: 3.9 does not work because of dependency conflicts
array=( 3.6 3.7 3.8 )

# Constants
MINICONDA=$HOME/miniconda3

echo "Building conda package ..."
cd ~
conda skeleton pypi $pkg

# update meta.yaml
echo "Updating meta.yaml ..."
sed -i 's/^\(\s\+- h3\)$/\1-py/g' $pkg/meta.yaml
sed -i 's/^\(\s\+-\) your-github-id-here/\1 18722560/g' $pkg/meta.yaml

# building conda packages
for i in "${array[@]}"
do
    echo "Building for Python $i"
	conda-build --python $i $pkg
done

# convert package to other platforms
cd ~
platforms=( osx-64 linux-32 linux-64 win-32 win-64 )
find $MINICONDA/conda-bld/linux-64/ -name *.tar.bz2 | while read file
do
    echo $file
    for platform in "${platforms[@]}"
    do
       conda convert --platform $platform $file  -o $MINICONDA/conda-bld/
    done    
done

# upload packages to conda
find $MINICONDA/conda-bld/ -name *.tar.bz2 | while read file
do
    echo $file
    anaconda upload $file
done
echo "Building conda package done!"

rm $HOME/h3pandas -r
conda build purge
