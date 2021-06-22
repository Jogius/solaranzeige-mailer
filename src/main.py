from dotenv import load_dotenv
from os import environ

def main():
  HOST = environ['DB_HOST']
  PORT = environ['DB_PORT']
  INTERVAL = environ['QUERY_INTERVAL']

if __name__ == '__main__':
  load_dotenv()
  main()
