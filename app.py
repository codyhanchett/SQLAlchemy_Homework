#Dependencies
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt

#Create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False})

#Reflect Database
Base = automap_base()
Base.prepare(engine, reflect = True)

#Save table references
Measure = Base.classes.measurement
Station = Base.classes.station

#Create session
session = Session(engine)

#Setup Flask
app = Flask(__name__)

# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d' 
# and return the minimum, average, and maximum temperatures for that range of dates
def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVG, and TMAX
    """
    
    return session.query(func.min(Measure.tobs), func.avg(Measure.tobs), func.max(Measure.tobs)).\
        filter(Measure.date >= start_date).filter(Measure.date <= end_date).all()

#Set Flask Routes

@app.route("/")
def main():
    """List all routes that are available."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def rain():
    """Return the JSON representation of your dictionary."""

    print("Received rain API request.")

    last_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measure.date))).all()
    max_date_string = last_date_query[0][0]
    max_date = dt.datetime.strptime(max_date_string, "%Y-%m-%d")

    
    begin_date = max_date - dt.timedelta(365)

    
    rain_data = session.query(func.strftime("%Y-%m-%d", Measure.date), Measure.prcp).\
        filter(func.strftime("%Y-%m-%d", Measure.date) >= begin_date).all()
    

    results_dict = {}
    for result in rain_data:
        results_dict[result[0]] = result[1]

    return jsonify(results_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""

    print("Received station API request.")

    #query stations list
    stations = session.query(Station).all()

    #create a list of dictionaries
    stations_list = []
    for station in stations:
        station_dict = {}
        station_dict["id"] = station.id
        station_dict["station"] = station.station
        station_dict["name"] = station.name
        station_dict["latitude"] = station.latitude
        station_dict["longitude"] = station.longitude
        station_dict["elevation"] = station.elevation
        stations_list.append(station_dict)

    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations for the previous year."""

    print("Received tobs API request.")

    #We find temperature data for the last year.  First we find the last date in the database
    last_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measure.date))).all()
    max_date_string = last_date_query[0][0]
    max_date = dt.datetime.strptime(max_date_string, "%Y-%m-%d")

    #set beginning of search query
    begin_date = max_date - dt.timedelta(365)

    #get temperature measurements for last year
    results = session.query(Measure).\
        filter(func.strftime("%Y-%m-%d", Measure.date) >= begin_date).all()

    #create list of dictionaries (one for each observation)
    tobs_list = []
    for result in results:
        tobs_dict = {}
        tobs_dict["date"] = result.date
        tobs_dict["station"] = result.station
        tobs_dict["tobs"] = result.tobs
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
def start(start):

    print("Received start date API request.")

    #First we find the last date in the database
    final_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measure.date))).all()
    max_date = final_date_query[0][0]

    #get the temperatures
    temps = calc_temps(start, max_date)

    #create a list
    return_list = []
    date_dict = {'start_date': start, 'end_date': max_date}
    return_list.append(date_dict)
    return_list.append({'Observation': 'TMIN', 'Temperature': temps[0][0]})
    return_list.append({'Observation': 'TAVG', 'Temperature': temps[0][1]})
    return_list.append({'Observation': 'TMAX', 'Temperature': temps[0][2]})

    return jsonify(return_list)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a given start
    or start-end range."""

    print("Received start date and end date API request.")

    #get the temperatures
    temps = calc_temps(start, end)

    #create a list
    return_list = []
    date_dict = {'start_date': start, 'end_date': end}
    return_list.append(date_dict)
    return_list.append({'Observation': 'TMIN', 'Temperature': temps[0][0]})
    return_list.append({'Observation': 'TAVG', 'Temperature': temps[0][1]})
    return_list.append({'Observation': 'TMAX', 'Temperature': temps[0][2]})

    return jsonify(return_list)

if __name__ == "__main__":
    app.run(debug = True)