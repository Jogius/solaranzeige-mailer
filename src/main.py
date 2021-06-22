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

def handleProblem(averages, plus, difference):
  pass

def main():
  HOST = environ['DB_HOST']
  PORT = environ['DB_PORT']
  INTERVAL = environ['QUERY_INTERVAL']
  MIN_PLUS = float(environ['MIN_PLUS'])
  MAX_DIFFERENCE = float(environ['MAX_DIFFERENCE'])
  MIN_SOC = float(environ['MIN_SOC'])

  # Create database connection
  client = getDatabaseClient(HOST, PORT)

  # Get averages from the database
  averages = getAverages(client, INTERVAL)

  # Calculate how much energy is generated and not used
  plus = averages['solarAvg'] - averages['consumptionAvg']

  # Calculate the difference between how much should be going into the battery
  # and how much is actually going in
  difference = abs(plus - averages['batteryAvg'])

  # Logging
  print(f'--------------------\n'
    ' - plus: {plus}\n'
    ' - batteryAvg: {averages["batteryAvg"]}\n'
    ' --> difference: {difference}\n'
    ' - socAvg: {averages["socAvg"]}')
  
  # If a certain amount of energy is left over, the battery has less than a certain
  # percentage of power and the difference between this leftover and how much is going
  # into the battery is too big, call a function to handle the problem case
  if plus >= MIN_PLUS and averages['socAvg'] <= MIN_SOC and difference > MAX_DIFFERENCE:
    handleProblem(averages, plus, difference)

  client.close()

if __name__ == '__main__':
  load_dotenv()
  main()
