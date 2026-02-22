-- Databricks notebook source
CREATE DATABASE IF NOT EXISTS s_consumidor;

CREATE EXTERNAL TABLE IF NOT EXISTS s_consumidor.consumidorservicosfinanceiros(
  gestor string, 
  canalorigem string, 
  regiao string, 
  uf string, 
  cidade string, 
  sexo string, 
  faixaetaria string, 
  anoabertura int, 
  mesabertura int, 
  dataabertura date, 
  dataresposta date, 
  dataanalise date, 
  datarecusa date, 
  datafinalizacao date, 
  prazoresposta date, 
  prazoanalisegestor int, 
  temporesposta int, 
  nomefantasia string, 
  segmentomercado string, 
  area string, 
  assunto string, 
  grupoproblema string, 
  problema string, 
  comocontratou string, 
  procurouempresa boolean, 
  respondida boolean, 
  situacao string, 
  avaliacaoreclamacao string, 
  notaconsumidor int, 
  analiserecusa string,
  datrefcarga string)
LOCATION
  's3://besga//data/s_consumidor/consumidorservicosfinanceiros';

GRANT SELECT ON TABLE s_consumidor.consumidorservicosfinanceiros TO `lucas_san20@hotmail.com`;
