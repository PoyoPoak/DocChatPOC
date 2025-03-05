# DocChat

docker network prune -f
docker pull mysql
docker network create mysql-net
docker run -d --name mysql-server --network mysql-net -p "3306:3306" -e "MYSQL_RANDOM_ROOT_PASSWORD=yes" -e "MYSQL_DATABASE=documents" -e "MYSQL_USER=admin" -e "MYSQL_PASSWORD=password" mysql
docker run --rm -it --network mysql-net mysql mysql -h mysql-server -u admin -p
USE documents;

docker pull mysql
docker-compose up -d
docker run --rm -it --network mysql-net mysql mysql -h mysql-server -u admin -p
USE documents;

python -m venv "./.env"
pip install -r requirements.txt