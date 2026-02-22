-- Databricks notebook source
CREATE DATABASE IF NOT EXISTS b_consumidor;

CREATE EXTERNAL TABLE IF NOT EXISTS b_consumidor.consumidor(
  gestor string, 
  canalorigem string, 
  regiao string, 
  uf string, 
  cidade string, 
  sexo string, 
  faixaetaria string, 
  anoabertura string, 
  mesabertura string, 
  dataabertura string, 
  dataresposta string, 
  dataanalise string, 
  datarecusa string, 
  datafinalizacao string, 
  prazoresposta string, 
  prazoanalisegestor string, 
  temporesposta string, 
  nomefantasia string, 
  segmentomercado string, 
  area string, 
  assunto string, 
  grupoproblema string, 
  problema string, 
  comocontratou string, 
  procurouempresa string, 
  respondida string, 
  situacao string, 
  avaliacaoreclamacao string, 
  notaconsumidor string, 
  analiserecusa string,
  datrefcarga string)
LOCATION
  's3://besga//data/b_consumidor/consumidor';

GRANT SELECT ON TABLE b_consumidor.consumidor TO `lucas_san20@hotmail.com`;
