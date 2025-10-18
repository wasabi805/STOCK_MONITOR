to run back end

cd backend
python3 -m venv venv
source venv/bin/activate # Windows: .\venv\Scripts\Activate.ps1

python manage.py startapp tracker

(venv) ocampo@Tims-MacBook-Pro backend % python manage.py runserver
