# ensure `pip install --target ...` works
echo "[install]
prefix=" > setup.cfg

mkdir -p deps
touch deps/__init__.py
pip install --target "./deps" -r deps.txt
