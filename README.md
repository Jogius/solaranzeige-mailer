# solaranzeige-mailer

A python program that reads data from a solaranzeige influxdb and sends an email if certain conditions are met

## Disclaimer

This script is can be used with a software called [solaranzeige](https://solaranzeige.de). However, it was created for my personal use and is not actively maintained, so compatibility with newer versions of solaranzeige is likely but not promised.

## Configuration

To configure the script, simply copy the `.env.example` file to `.env` and replace the values with your own.

## Description

The script averages the data from solaranzeige in the last x minutes and checks for a certain case: if more energy is produced than used, there is room left in the battery and too little of that leftover power is going to the battery, an email is sent to notify the user.
