from dotenv import load_dotenv
from os import environ
from influxdb import InfluxDBClient

def getDatabaseClient(host, port):
  return InfluxDBClient(host=host, port=port, database='solaranzeige')

def getAverages(client, interval):
  result = client.query(f'''
    SELECT MEAN(Verbrauch) FROM AC WHERE time > now() - {interval}m;
    SELECT MEAN(Leistung) FROM PV WHERE time > now() - {interval}m;
    SELECT MEAN(Leistung) FROM Batterie WHERE time > now() - {interval}m;
    SELECT MEAN(User_SOC) FROM Batterie WHERE time > now() - {interval}m;
  ''')

  return {
    'consumptionAvg': next(result[0].get_points(measurement='AC'))['mean'],
    'solarAvg': next(result[1].get_points(measurement='PV'))['mean'],
    'batteryAvg': -(next(result[2].get_points(measurement='Batterie'))['mean']),
    'socAvg': next(result[3].get_points(measurement='Batterie'))['mean']
  }

def main():
  HOST = environ['DB_HOST']
  PORT = environ['DB_PORT']
  INTERVAL = environ['QUERY_INTERVAL']

  client = getDatabaseClient(HOST, PORT)

  averages = getAverages(client, INTERVAL)

  client.close()

if __name__ == '__main__':
  load_dotenv()
  main()
