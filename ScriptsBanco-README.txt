O código, assim que executado, cria automaticamente o banco de dados na pasta do projeto.

Usuário administrador - User:admin senha:admin
Usuário comum - User:comum senha:comum
Todo usuário novo criado é automaticamente comum.

-- Script para criar o banco de dados
CREATE DATABASE IF NOT EXISTS pokemon_db;
USE pokemon_db;

-- Script para criar a tabela 'tipo'
CREATE TABLE IF NOT EXISTS tipo (
    Nome varchar(50) PRIMARY KEY
);

-- Script para criar a tabela 'pokemon'
CREATE TABLE IF NOT EXISTS pokemon (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome varchar(50) NOT NULL,
    Tipo1 varchar(50) NOT NULL,
    Tipo2 varchar(50),
    Vida INTEGER,
    Ataque INTEGER,
    Defesa INTEGER,
    AtaqueEspecial INTEGER,
    DefesaEspecial INTEGER,
    Velocidade INTEGER,
    FOREIGN KEY (Tipo1) REFERENCES tipo (Nome),
    FOREIGN KEY (Tipo2) REFERENCES tipo (Nome)
);

-- Script para criar a tabela 'users'
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL
);
