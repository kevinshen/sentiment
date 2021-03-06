from sqlalchemy import *
from sqlalchemy.orm import *
from scraper import scraper
from models import day
from datetime import timedelta, date as d, datetime


def create_table(table_name):
    """
    Creates the table.
    :return: None
    """
    db = create_engine("sqlite:///db/app.db", echo=False)
    metadata = MetaData(db)

    days = Table(table_name, metadata,
                 Column("id", Integer, primary_key=True),
                 Column("date", Date, nullable=False),
                 Column("sentiment", Float, nullable=False),
                 Column("comment1", String, nullable=False),
                 Column("comment1_url", String, nullable=False),
                 Column("comment1_title", String, nullable=False),
                 Column("comment2", String, nullable=False),
                 Column("comment2_url", String, nullable=False),
                 Column("comment2_title", String, nullable=False),
                 Column("comment3", String, nullable=False),
                 Column("comment3_url", String, nullable=False),
                 Column("comment3_title", String, nullable=False)
                 )

    days.create()


def delete_table(table_name):
    """
    Deletes all data.
    :return: None
    """
    db = create_engine("sqlite:///db/app.db", echo=False)
    metadata = MetaData(db)
    days = Table(table_name, metadata, autoload=True)

    days.drop(db)


def add_entry(table_name, date):
    """
    Adds an entry for the specified day/week/month/year.
    Includes date, comments, article urls, and article titles.
    :param date: the date to be added.
    :return: None
    """
    db = create_engine("sqlite:///db/app.db", echo=False)
    metadata = MetaData(db)
    days = Table(table_name, metadata, autoload=True)

    clear_mappers()

    mapper(day.Day, days)

    session = Session()

    comment_index = 0
    url_index = 2
    num_days = 1

    if table_name == "weeks":
        num_days = 7
        iso_date = date.isocalendar()
        date = iso_to_gregorian(iso_date[0],iso_date[1],7)

    elif table_name == "months":
        if date.month == 12: 
            date = d(date.year, 12, 31)
        else:
            date = d(date.year, date.month + 1, 1) - timedelta(days=1)
        num_days = (date - d(date.year, date.month, 1)).days + 1

    elif table_name == "years":
        date = d(date.year, 12, 31)
        if date > d.today():
            date = d.today()
        num_days = (date - d(date.year, 1, 1)).days + 1

    sentiment, top_comments, top_votes, titles = scraper.analyze(date, num_days)

    # date indicates the first day of the week, month, or year analyzed
    today = day.Day(date=date - timedelta(days=num_days-1),
                       sentiment=sentiment.polarity,
                       comment1=top_comments[1][comment_index],
                       comment1_url=top_comments[1][url_index],
                       comment1_title=titles[1],
                       comment2=top_comments[2][comment_index],
                       comment2_url=top_comments[2][url_index],
                       comment2_title=titles[2],
                       comment3=top_comments[3][comment_index],
                       comment3_url=top_comments[3][url_index],
                       comment3_title=titles[3],
                       )
    session.add(today)
    session.commit()
    session.flush()


def delete_entry(table_name, date):
    """
    Deletes the entry on a date.
    :param date: the date to remove.
    :return: None
    """
    db = create_engine("sqlite:///db/app.db", echo=False)
    metadata = MetaData(db)
    days = Table(table_name, metadata, autoload=True)

    d = days.delete(days.c.date == date)
    d.execute()


def display_table(table_name):
    """
    Displays the entire table.
    :return: None
    """
    db = create_engine("sqlite:///db/app.db", echo=False)

    metadata = MetaData(db)

    # The table of data
    days = Table(table_name, metadata, autoload=True)

    s = days.select()
    rs = s.execute()

    for row in rs:
        print(row)


def get_entry(table_name, date):
    """
    Gets an entry from a specific date.
    :param date: the date of the entry to get.
    :return: the row in the table selected.
    """
    db = create_engine("sqlite:///db/app.db", echo=False)
    metadata = MetaData(db)
    days = Table(table_name, metadata, autoload=True)

    iso_date = date.isocalendar()
    if table_name == "weeks":
        date = iso_to_gregorian(iso_date[0],iso_date[1],1)
    elif table_name == "months":
        date = d(date.year, date.month, 1)
    elif table_name == "years":
        date = d(date.year, 1, 1)

    selection = days.select(days.c.date == date)
    rs = selection.execute()

    for row in rs:
        entry = row
    return entry


def display_entry(selection):
    """
    Displays an entry in the table.
    :param selection: the selected entry.
    :return: None
    """
    rs = selection.execute()
    for row in rs:
        print(row)

def update_tables():
    """
    Updates all tables each day.
    :return: None
    """
    date = d.today()

    delete_entry("days", date)
    delete_entry("weeks", date)
    delete_entry("months", date)
    delete_entry("years", date)

    add_entry("days", date)
    add_entry("days", date)
    add_entry("days", date)
    add_entry("days", date)


def iso_year_start(iso_year):
    """
    The gregorian calendar date of the 
    first day of the given ISO year.
    :return: date object
    """
    fourth_jan = d(iso_year, 1, 4)
    delta = timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta 


def iso_to_gregorian(iso_year, iso_week, iso_day):
    """
    Gregorian calendar date for the 
    given ISO year, week and day.
    :return: date object
    """
    year_start = iso_year_start(iso_year)
    return year_start + timedelta(days=iso_day-1, weeks=iso_week-1)


def get_mood(sentiment):

    if sentiment <= -0.7:
        mood = "Terrible &#x1F621;"
        color = "#ff4c40"
    elif sentiment > -0.7 and sentiment <= -0.4:
        mood = "Bad &#x1F625;"
        color = "#ff6459"
    elif sentiment > -0.4 and sentiment <= -0.1:
        mood = "Meh &#x1F615;"
        color = "#ff9359"
    elif sentiment == 0.0:
        mood = "Sleeping &#x1f634"
        color = "#808080"
    elif sentiment > -0.1 and sentiment <= 0.1:
        mood = "Neutral &#x1F610;"
        color = "#fdd835"
    elif sentiment > 0.1 and sentiment <= 0.4:
        mood = "Fine &#x1F600;"
        color = "#a9e66c"
    elif sentiment > 0.4 and sentiment <= 0.7:
        mood = "Cheery &#x1F60E;"
        color = "#50e582"
    else:
        mood = "Ecstatic &#x1F60D;"
        color = "#4ce659"

    return mood, color


def main():
    """
    Tests the database.
    :return: None
    """
    #display_table("days")
    #display_table("weeks")
    display_table("months")
    #display_table("years")

if __name__ == "__main__":
    main()