# Import the dependencies.
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt

#################################################
# Database Setup
#################################################
# Create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database into ORM classes
Base = automap_base()
Base.prepare(autoload_with=engine)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

# Calculate one_year_ago since it will be used in multiple routes
one_year_ago = dt.datetime.strptime(
    session.query(func.max(Measurement.date)).scalar(), "%Y-%m-%d"
) - dt.timedelta(days=366)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
# Define the homepage route
@app.route("/")
def welcome():
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )


# Define the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    precipitation_data = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_year_ago)
        .all()
    )
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)


# Define the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():
    stations_data = session.query(Station.station).all()
    stations_list = [station[0] for station in stations_data]
    return jsonify(stations_list)


# Define the /api/v1.0/tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    the_most_active = (
        session.query(Measurement.station)
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()[0]
    )
    tobs_data = (
        session.query(Measurement.tobs)
        .filter(Measurement.station == the_most_active)
        .filter(Measurement.date >= one_year_ago)
        .all()
    )  # Use the most active station's ID
    tobs_list = [tobs[0] for tobs in tobs_data]
    return jsonify(tobs_list)


# Define the /api/v1.0/<start> and /api/v1.0/<start>/<end> routes
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start, end=None):
    max_date = dt.datetime.strptime(
        session.query(func.max(Measurement.date)).scalar(), "%Y-%m-%d"
    ).date()
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
    except ValueError:
        return (
            jsonify({"error": "Invalid start date format. Please use YYYY-MM-DD."}),
        )
    if start_date > max_date:
        return "The start date is greater than the max date in the database!"
    elif end:
        try:
            end_date = dt.datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify({"error": "Invalid end date format. Please use YYYY-MM-DD."}),
            )
        if start_date > end_date:
            return "The start date is greater than the end date!"
        query = (
            session.query(
                func.min(Measurement.tobs),
                func.avg(Measurement.tobs),
                func.max(Measurement.tobs),
            )
            .filter(Measurement.date >= start_date)
            .filter(Measurement.date <= end_date)
        )
    else:
        query = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs),
        ).filter(Measurement.date >= start_date)

    results = query.all()
    temp_stats = {"TMIN": results[0][0], "TAVG": results[0][1], "TMAX": results[0][2]}
    return jsonify(temp_stats)


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
