mkdir -p py
cp ../static/py/* py/
cp -r ../static/ll_os_path/ .
python ../../../../bin/flexcompile.py chimp.py flash_main
