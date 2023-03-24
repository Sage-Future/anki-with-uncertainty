rm -r build

mkdir build
cp __init__.py build/__init__.py

mkdir build/user_files 
cp README.md build/user_files/README.md

cd build
zip -r ../ankiwithuncertainty.ankiaddon *

echo "Created ankiwithuncertainty.ankiaddon"
