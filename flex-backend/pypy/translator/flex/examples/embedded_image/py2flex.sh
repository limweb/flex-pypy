mkdir -p py
cp -fr ../static/py/* py/
cp -fr ../static/ll_os_path .
python ../../../../bin/flexcompile.py embed.py flash_main
