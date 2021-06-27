# /bin/bash
make clean
cp -r ../notebook/* source/notebook
make html 
# rm -r source/notebook
xdg-open build/html/index.html
