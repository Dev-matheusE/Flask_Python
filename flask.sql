CREATE DATABASE estudante_db;

USE estudante_db;

CREATE TABLE estudante (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    matrícula VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL
);


