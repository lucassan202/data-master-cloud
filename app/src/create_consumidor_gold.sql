-- Databricks notebook source
CREATE DATABASE IF NOT EXISTS g_consumidor;

CREATE EXTERNAL TABLE IF NOT EXISTS g_consumidor.grupoProblema(
  nomefantasia string, 
  grupoproblema string, 
  datrefcarga string, 
  qtdreclamcoes bigint)
LOCATION
  's3://besga//data/g_consumidor/grupoproblema';

GRANT SELECT ON TABLE g_consumidor.grupoProblema TO `lucas_san20@hotmail.com`;

CREATE EXTERNAL TABLE IF NOT EXISTS g_consumidor.mediaavaliacao(
  nomefantasia string, 
  datrefcarga string, 
  mediaAvaliacao double)
LOCATION
  's3://besga//data/g_consumidor/mediaavaliacao';

GRANT SELECT ON TABLE g_consumidor.mediaavaliacao TO `lucas_san20@hotmail.com`;

CREATE EXTERNAL TABLE IF NOT EXISTS g_consumidor.mediaresposta(
  nomefantasia string, 
  datrefcarga string, 
  mediaRespostaDias double)
LOCATION
  's3://besga//data/g_consumidor/mediaresposta';

GRANT SELECT ON TABLE g_consumidor.mediaresposta TO `lucas_san20@hotmail.com`;

CREATE EXTERNAL TABLE IF NOT EXISTS g_consumidor.reclamacaotopten(
  nomefantasia string, 
  datrefcarga string, 
  qtdreclamcoes bigint)
LOCATION
  's3://besga//data/g_consumidor/reclamacaotopten';

GRANT SELECT ON TABLE g_consumidor.reclamacaotopten TO `lucas_san20@hotmail.com`;

CREATE EXTERNAL TABLE IF NOT EXISTS g_consumidor.reclamacaouf(
  nomefantasia string, 
  uf string,
  datrefcarga string, 
  qtdReclamcoesUf bigint)
LOCATION
  's3://besga//data/g_consumidor/reclamacaouf';

GRANT SELECT ON TABLE g_consumidor.reclamacaouf TO `lucas_san20@hotmail.com`;
