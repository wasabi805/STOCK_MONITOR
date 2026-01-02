to run back end

#run virtual environment
cd backend
source venv/bin/activate // run virt env

# For Windows: .\venv\Scripts\Activate.ps1

python manage.py startapp tracker

(venv) ocampo@Tims-MacBook-Pro backend % python manage.py runserver

health check : http://127.0.0.1:8000/api/stock/AAPL/

may not work with the free plan
http://127.0.0.1:8000/api/history/AAPL/?resolution=1&days=5

# Running daphne

Activate your venv and use the venv’s Python to run daphne:

cd backend
source venv/bin/activate # make sure you see (venv)
which python # should point to backend/venv/bin/python
which daphne # ideally backend/venv/bin/daphne

If daphne isn’t in the venv yet, install it (and DRF) inside the venv:

pip install daphne channels djangorestframework
pip freeze > requirements.txt

# Start via the venv interpreter (this guarantees the right environment):

!! ---> python -m daphne -p 8000 stock_monitor.asgi:application

to check, visit : http://127.0.0.1:8000/api/stock/AAPL/

# view normailized data in browser

ex.) ws://127.0.0.1:8000/ws/quotes/AAPL/

# To Test

open another terminal and run

# Note testing for stocks in real time will only work when the market is open, not on the weekends

cd backend
python3 -m http.server 8080
then visit http://127.0.0.1:8080/test_ws.html

# To test Bitcoin (24/7)

cd backend
python3 -m http.server 8080
then visit http://127.0.0.1:8080/test_ws_btc.html
