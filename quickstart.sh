#!/bin/bash

pushd ../
git clone git@github.com:mach327/chirp_fork.git
git clone git@github.com:mach327/md380tools.git
popd 

virtualenv env -p python2
source env/bin/activate
pip install -r requirements.txt

pushd drivers/
ln -s ../../md380tools/chirp/md380.py
popd
echo "You will have to source the python virtualenv like so:"
echo "source env/bin/activate"
