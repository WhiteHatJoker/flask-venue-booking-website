# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ---------------
# -------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), primary_key=True, unique=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), primary_key=True, unique=False)
    start_time = db.Column(db.DateTime, nullable=False)


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500))
    artists = db.relationship('Show', passive_deletes=True, backref='venues', lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500))
    venues = db.relationship('Show', backref='artists', passive_deletes=True, lazy=True)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
# ----------------------------------------------------------------#

# Listing all venues
@app.route('/venues')
def venues():
    all_areas = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    data = []
    today = datetime.utcnow()
    for area in all_areas:
        area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
        venue_data = []
        for venue in area_venues:
            venue_data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > today).count()
            })
        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venue_data
        })
    return render_template('pages/venues.html', areas=data)


# Search for a venue by its name with partial string search (case-insensitive)
@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venue_search_results = Venue.query.with_entities(Venue.id, Venue.name).filter(Venue.name.ilike("%" + search_term + "%")).all()
    response = {'data': venue_search_results, 'count': len(venue_search_results)}
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


# Listing a specific venue information
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    past_shows = []
    upcoming_shows = []
    now = datetime.utcnow()
    venue = Venue.query.get(venue_id)

    past_shows_query = db.session.query(Artist.id, Artist.name, Artist.image_link, Show.start_time)\
        .join(Show, Artist.id == Show.artist_id)\
        .filter(Show.venue_id == venue_id).filter(Show.start_time > now).all()
    upcoming_shows_query = db.session.query(Artist.id, Artist.name, Artist.image_link, Show.start_time) \
        .join(Show, Artist.id == Show.artist_id) \
        .filter(Show.venue_id == venue_id).filter(Show.start_time < now).all()

    for past_show in past_shows_query:
        past_shows.append({
            'artist_id': past_show.id,
            'artist_name': past_show.name,
            'artist_image_link': past_show.image_link,
            'start_time': past_show.start_time.strftime("%A %B %d %Y %I:%M %p")
        })
    for future_show in upcoming_shows_query:
        upcoming_shows.append({
            'artist_id': future_show.id,
            'artist_name': future_show.name,
            'artist_image_link': future_show.image_link,
            'start_time': future_show.start_time.strftime("%A %B %d %Y %I:%M %p")
        })

    data = {
        "id": venue_id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "image_link": venue.image_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "upcoming_shows_count": len(upcoming_shows),
        "past_shows_count": len(past_shows)
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


# Creating a new venue
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    name = request.form['name']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    genres = ",".join(request.form.getlist('genres'))
    seeking_talent = True if request.form.get('seeking_talent') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_talent == True else None
    try:
        new_venue = Venue(name=name, address=address, city=city, state=state, phone=phone, image_link=image_link,
                          facebook_link=facebook_link, website=website, genres=genres, seeking_talent=seeking_talent,
                          seeking_description=seeking_description
                          )
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('Venue ' + request.form['name'] + ' cannot be added!')
    finally:
        db.session.close()
    return redirect(url_for('venues'))


# Deleting a specific venue
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        error = False
        venue = Venue.query.get(venue_id)
        name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {name} was successfully deleted.')
    except:
        db.session.rollback()
        flash(f'An error occurred. Venue {name} could not be deleted.')
        error = True
    finally:
        db.session.close()
        return jsonify({'success': not error})


#  Artists
#  ----------------------------------------------------------------


# Listing all artists
@app.route('/artists')
def artists():
    return render_template('pages/artists.html', artists=Artist.query.with_entities(Artist.id, Artist.name).order_by('id').all())


# Searching artist by his name
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artist_search_results = Artist.query.with_entities(Artist.id, Artist.name).filter(Artist.name.ilike("%" + search_term + "%")).all()
    data = []
    now = datetime.utcnow()
    for artist in artist_search_results:
        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': db.session.query(Show).filter(Show.artist_id == artist.id).filter(Show.start_time > now).count()
        })
    response = {
        'data': data,
        'count': len(artist_search_results)
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


# Listing information about a specific artist
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    past_shows = []
    upcoming_shows = []
    now = datetime.utcnow()
    artist = Artist.query.get(artist_id)

    past_shows_query = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time)\
        .join(Show, Venue.id == Show.venue_id)\
        .filter(Show.artist_id == artist_id).filter(Show.start_time > now).all()
    upcoming_shows_query = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time) \
        .join(Show, Venue.id == Show.venue_id) \
        .filter(Show.artist_id == artist_id).filter(Show.start_time < now).all()

    for past_show in past_shows_query:
        past_shows.append({
            'venue_id': past_show.id,
            'venue_name': past_show.name,
            'venue_image_link': past_show.image_link,
            'start_time': past_show.start_time.strftime("%A %B %d %Y %I:%M %p")
        })
    for future_show in upcoming_shows_query:
        upcoming_shows.append({
            'venue_id': future_show.id,
            'venue_name': future_show.name,
            'venue_image_link': future_show.image_link,
            'start_time': future_show.start_time.strftime("%A %B %d %Y %I:%M %p")
        })

    data = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "upcoming_shows_count": len(upcoming_shows),
        "past_shows_count": len(past_shows)
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.image_link.data = artist.image_link
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website
    form.genres.data = artist.genres
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    return render_template('forms/edit_artist.html', form=form, artist=artist)


# Updating information about a specific artist
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    seeking_venue = True if request.form.get('seeking_venue') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_venue == True else None
    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.website = request.form['website']
        artist.genres = ",".join(request.form.getlist('genres'))
        artist.seeking_venue = seeking_venue
        artist.seeking_description = seeking_description

        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('Artist ' + request.form['name'] + ' cannot be updated!')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.name.data = venue.name
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.image_link.data = venue.image_link
    form.facebook_link.data = venue.facebook_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    return render_template('forms/edit_venue.html', form=form, venue=venue)


# Updating information about a specific venue
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    seeking_talent = True if request.form.get('seeking_talent') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_talent == True else None
    try:
        venue.name = request.form['name']
        venue.address = request.form['address']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.website = request.form['website']
        venue.genres = ",".join(request.form.getlist('genres'))
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('Venue ' + request.form['name'] + ' cannot be updated!')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


# Creating a new artist
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    genres = ",".join(request.form.getlist('genres'))
    seeking_venue = True if request.form.get('seeking_venue') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_venue == True else None
    try:
        new_artist = Artist(name=name, city=city, state=state, phone=phone, image_link=image_link,
                            facebook_link=facebook_link, website=website, genres=genres, seeking_venue=seeking_venue,
                            seeking_description=seeking_description
                            )
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + name + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('Artist ' + name + ' cannot be added!')
    finally:
        db.session.close()
    return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------

# Listing all shows
@app.route('/shows')
def shows():
    data = []
    shows = db.session.query(Show.venue_id, Show.artist_id, Show.start_time, Venue.name.label("venue_name"), Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"))\
        .join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).all()
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue_name,
            "artist_id": show.artist_id,
            "artist_name": show.artist_name,
            "artist_image_link": show.artist_image_link,
            "start_time": show.start_time.strftime("%A %B %d %Y %I:%M %p")
        })
    return render_template('pages/shows.html', shows=data)


# Renders create show form
@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


# Creating a new show
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    venue_id = request.form['venue_id']
    artist_id = request.form['artist_id']
    start_time = request.form['start_time']
    venue = Venue.query.get(venue_id)
    artist = Artist.query.get(artist_id)
    if venue and artist:
        try:
            new_show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
            db.session.add(new_show)
            db.session.commit()
            flash('Your show was successfully listed!')
        except:
            db.session.rollback()
            flash('Your show cannot be added. Please try again')
        finally:
            db.session.close()
    else:
        flash("The Artist or Venue with a given ID doesn't exist. Please check the ID and create a show again")
    return redirect(url_for('shows'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
