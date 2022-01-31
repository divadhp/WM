export DISPLAY=:0
Xephyr -ac -br -screen 1200x800 :2 &
export DISPLAY=:2
python window_manager.py
