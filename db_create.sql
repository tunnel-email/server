CREATE DATABASE service_db;
CREATE USER 'registrator'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON service_db.* TO 'registrator'@'localhost';
FLUSH PRIVILEGES;


USE service_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    yandex_id VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL,
    UNIQUE KEY unique_user_token (yandex_id, token)
);
