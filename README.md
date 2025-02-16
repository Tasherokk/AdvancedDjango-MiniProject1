# AdvancedDjango-MiniProject1

Steps to run project
1. docker-compose up -d --build
2. docker-compose run web python manage.py makemigrations
3. docker-compose run web python manage.py migrate


May be needed
1. docker-compose restart web (to restart)
2. docker-compose down (to turn off) 
3. docker-compose build (to build)   
4. docker-compose up -d (to turn on)  
5. docker-compose up -d --remove-orphans (to remove old containers)
6. docker-compose exec web pip install crispy-bootstrap4 (to install additional libraries or modules)
