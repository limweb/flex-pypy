mkdir -p py
cp -r ../static/py/* py/
cp -r ../static/ll_os_path .
python ../../../../bin/flexcompile.py button.py flash_main
