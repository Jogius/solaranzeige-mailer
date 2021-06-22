from dotenv import load_dotenv
from os import environ
from influxdb import InfluxDBClient

def getDatabaseClient(host, port):
  return InfluxDBClient(host=host, port=port, database='solaranzeige')

def main():
  HOST = environ['DB_HOST']
  PORT = environ['DB_PORT']
  INTERVAL = environ['QUERY_INTERVAL']

  client = getDatabaseClient(HOST, PORT)

  client.close()

if __name__ == '__main__':
  load_dotenv()
  main()
