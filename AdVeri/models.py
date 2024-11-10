from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(db.String(16), nullable=False)
    role = db.Column(db.String, nullable=False)
    sponsor = db.relationship('Sponsor', backref='user', lazy=True, cascade="all, delete-orphan")
    influencer = db.relationship('Influencer', backref='user', lazy=True, cascade="all, delete-orphan")
    flagged = db.relationship('Flagged', backref='user', lazy=True, cascade="all, delete-orphan")

class Sponsor(db.Model):
    __tablename__ = 'sponsors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(120), unique = True, nullable = False)
    industry = db.Column(db.String(120), nullable = False)
    budget = db.Column(db.Float, nullable = False)
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True, cascade="all, delete-orphan")
    requests = db.relationship('AdRequest', backref='sponsor', lazy=True, cascade="all, delete-orphan")

class Influencer(db.Model):
    __tablename__ = 'influencers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), unique = True, nullable=False)
    category = db.Column(db.String(120), nullable=False)
    niche = db.Column(db.String(120), nullable=False)
    reach = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String, nullable=False)
    earnings = db.Column(db.Float, default = 0, nullable = False)
    ad_requests = db.relationship('AdRequest', backref='influencer', lazy=True, cascade="all, delete-orphan")

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.user_id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(20), nullable=False)
    goals = db.Column(db.Text, nullable=False)
    ad_requests = db.relationship('AdRequest', backref='campaign', lazy=True, cascade="all, delete-orphan")
    flagged = db.relationship('Flagged', backref='campaign', lazy=True, cascade="all, delete-orphan")

class AdRequest(db.Model):
    __tablename__ = 'ad_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.user_id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencers.user_id'), nullable=False)
    messages = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    negotiated_amount = db.Column(db.Float, default = 0, nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Flagged(db.Model):
    __tablename__ = 'flagged'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
