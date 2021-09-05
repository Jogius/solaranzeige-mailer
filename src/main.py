from dotenv import load_dotenv
from os import environ
from pathlib import Path
from time import sleep
from influxdb import InfluxDBClient
from smtplib import SMTP_SSL as SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    'consumptionAvg': round(next(result[0].get_points(measurement='AC'))['mean'], 1),
    'solarAvg': round(next(result[1].get_points(measurement='PV'))['mean'], 1),
    'batteryAvg': -(round(next(result[2].get_points(measurement='Batterie'))['mean'], 1)),
    'socAvg': round(next(result[3].get_points(measurement='Batterie'))['mean'], 1)
  }

def getSMTPConnection(host, port, username, password):
  connection = SMTP(host, port)
  connection.login(username, password)
  return connection

def lock():
  LOCK.touch()
  sleep(environ["EMAIL_INTERVAL"] * 60)
  LOCK.unlink()

def handleProblem(averages, plus, difference, data):
  HOST = environ['SMTP_HOST']
  PORT = environ['SMTP_PORT']
  USERNAME = environ['SMTP_USERNAME']
  PASSWORD = environ['SMTP_PASSWORD']
  SENDER = environ['MAIL_SENDER']
  RECIPIENT = environ['MAIL_RECIPIENT']
  SUBJECT = environ['MAIL_SUBJECT']

  email = MIMEMultipart()
  email['From'] = SENDER
  email['To'] = RECIPIENT
  email['Subject'] = SUBJECT
  email.attach(MIMEText('In den letzten 10 Minuten wurde mehr PV Überschuss erzeugt als in die Batterie geladen, obwohl der SoC unter 96% liegt.\nEin Balancing erscheint erforderlich.\n\n' + data + '\n(Durschnittswerte der letzten 10 Minuten)\n\nGeneriert von solaranzeige-mailer (https://github.com/Jogius/solaranzeige-mailer)\n© Julius Makowski\n'))

  mailServer = getSMTPConnection(HOST, PORT, USERNAME, PASSWORD)

  mailServer.sendmail(SENDER, RECIPIENT, email.as_string())

  mailServer.quit()

  lock()

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
  excess = round(averages['solarAvg'] - averages['consumptionAvg'], 1)

  # Calculate the difference between how much should be going into the battery
  # and how much is actually going in
  difference = round(excess - averages['batteryAvg'], 1)

  # String with important data
  data = f' - PV Überschuss: {excess}\n - Ladung der Batterie: {averages["batteryAvg"]}\n --> Differenz: {difference}\n - SoC: {averages["socAvg"]}'

  # Logging
  print(f'------------------------------\n' + data)
  
  # If a certain amount of energy is left over, the battery has less than a certain
  # percentage of power and the difference between this leftover and how much is going
  # into the battery is too big, call a function to handle the problem case
  if excess >= MIN_PLUS and averages['socAvg'] <= MIN_SOC and difference > MAX_DIFFERENCE:
    handleProblem(averages, excess, difference, data)

  client.close()

if __name__ == '__main__':
  load_dotenv()
  LOCK = Path(environ["EMAIL_LOCK"])
  if LOCK.exists():
    exit(0)
  main()
