from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from models import db, Users, Sponsor, Influencer, Campaign, AdRequest, Flagged
import pytz, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import date, datetime
from sqlalchemy import func

app = Flask(__name__)

app.config['SECRET_KEY'] = 'wet89nfwe9th29rh'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iescp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    admin_user = Users.query.filter_by(username = 'admin').first()
    if not admin_user:
        admin = Users(username = 'admin', password = 'root', role = 'Admin')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register/sponsors', methods = ['GET', 'POST'])
def register_sponsors():
    if request.method == 'POST':
        role = 'Sponsor'
        username = request.form.get('username').strip() if request.form.get('username') else None
        password = request.form.get('password').strip() if request.form.get('password') else None
        company_name = request.form.get('company_name').strip() if request.form.get('company_name') else None
        industry = request.form.get('industry').strip() if request.form.get('industry') else None
        budget = request.form.get('budget').strip() if request.form.get('budget') else None
        
        ## Validate required fields
        if not all([username, password, company_name, industry, budget]):
            flash('All fields are required.', 'error')
            return render_template('register_sponsors.html')
        
        ## Check if username already exists
        result = Users.query.filter_by(username = username).first()
        if result:
            flash('Username already exists.', 'error')
            return render_template('register_sponsors.html')
        
        ## Create and save the new user
        new_user = Users(username = username, password = password, role = role)
        db.session.add(new_user)
        db.session.commit()
        sponsor_id = new_user.id
        new_sponsor = Sponsor(user_id = sponsor_id, company_name = company_name, industry = industry, budget = budget)
        db.session.add(new_sponsor)
        db.session.commit()
        
        flash('Sponsor registered successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register_sponsors.html')

@app.route('/register/influencers', methods = ['GET', 'POST'])
def register_influencers():
    if request.method == 'POST':
        role = 'Influencer'
        username = request.form.get('username').strip() if request.form.get('username') else None
        password = request.form.get('password').strip() if request.form.get('password') else None
        name = request.form.get('name').strip() if request.form.get('name') else None
        category = request.form.get('category').strip() if request.form.get('category') else None
        niche = request.form.get('niche').strip() if request.form.get('niche') else None
        reach = request.form.get('reach').strip() if request.form.get('reach') else None
        platform = request.form.get('platform').strip() if request.form.get('platform') else None

        if not all([username, password, name, category, niche, reach, platform]):
            flash('All fields are required.', 'error')
            return render_template('register_influencers.html')

        result = Users.query.filter(Users.username == username).first()
        if result:
            flash('Username already exists.', 'error')
            return render_template('register_influencers.html')

        new_user = Users(username = username, password = password, role = role)
        db.session.add(new_user)
        db.session.commit()

        influencer_id = new_user.id
        new_influencer = Influencer(user_id = influencer_id, name = name, category = category, niche = niche, reach = reach, platform = platform)
        db.session.add(new_influencer)
        db.session.commit()

        flash('Influencer registered successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register_influencers.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        user = Users.query.filter_by(username = username).first()
        if user and user.password == password:
            session['user_id'], session['role'] = user.id, user.role
            flagged_user = Flagged.query.filter(Flagged.user_id == session['user_id']).first()
            if not flagged_user:
                if session['role'] == 'Admin':
                    return redirect(url_for('admin_dashboard'))
                if session['role'] == 'Sponsor':
                    return redirect(url_for('sponsor_dashboard'))
                if session['role'] == 'Influencer':
                    return redirect(url_for('influencer_dashboard'))    
            else:
                flash(f'Your account has been flagged for {flagged_user.reason}. Please contact an admin/support for further assistance.', 'error')
                return redirect(url_for('login'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

'''__________________________________________________________Admin_Routes__________________________________________________________'''

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    try:
        ## Cards
        sponsors_count = Users.query.outerjoin(Flagged, Users.id == Flagged.user_id).filter(Users.role == 'Sponsor', Flagged.user_id == None).all()
        influencers_count = Users.query.outerjoin(Flagged, Users.id == Flagged.user_id).filter(Users.role == 'Influencer', Flagged.user_id == None).all()
        campaigns_count = Campaign.query.outerjoin(Flagged, Campaign.id == Flagged.campaign_id).filter(Flagged.campaign_id == None).all()

        ## Charts
        ## Share of campaign across all industries
        industry_data = db.session.query(Sponsor.industry, db.func.count(Campaign.id)).join(Campaign, Campaign.sponsor_id == Sponsor.user_id).group_by(Sponsor.industry).all()
        camp_by_industry = {industry: int(count) for industry, count in industry_data}

        ## Create the pie chart
        plt.clf()
        sizes = list(camp_by_industry.values())
        labels = list(camp_by_industry.keys())
        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.title('Campaign count by industry')
        plt.axis('equal')
        campaign_by_industry_path = 'images/campaign_by_industry.png'
        plt.savefig(f'static/{campaign_by_industry_path}')
        plt.close()

        ## Distribution of Sponsor and Influencer across industries.
        industries = list(camp_by_industry.keys())
        sponsors_counts = [len(Sponsor.query.filter_by(industry=industry).all()) for industry in industries]
        influencers_counts = [len(Influencer.query.filter(Influencer.category == industry).all()) for industry in industries]

        ## Data for the bar graph
        bar_width = 0.4
        index = range(len(industries))
        ut_orange, dartmouth_green = '#FF8200', '#00703C'

        ## Plotting the bar graph
        plt.clf()
        plt.figure(figsize=(8, 6))
        plt.bar(index, sponsors_counts, bar_width, label='Sponsor', color=ut_orange)
        plt.bar([i + bar_width for i in index], influencers_counts, bar_width, label='Influencer', color=dartmouth_green)

        ## Adding labels and title
        plt.xlabel('Industry')
        plt.ylabel('Count')
        plt.title('Sponsor and Influencer by Industry')
        plt.xticks([i + bar_width / 2 for i in index], industries)
        plt.legend()
        inf_and_spons_by_industry_path = 'images/inf_and_spons_by_industry.png'
        plt.savefig(f'static/{inf_and_spons_by_industry_path}')
        plt.close()

        return render_template('admin/dashboard.html',
                               sponsors_count=len(sponsors_count),
                               influencers_count=len(influencers_count),
                               campaigns_count=len(campaigns_count),
                               campaign_by_industry_path=campaign_by_industry_path,
                               inf_and_spons_by_industry_chart=inf_and_spons_by_industry_path)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/dashboard.html')

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        if action == 'flag':
            reason = request.form.get('reason', 'No reason provided.').strip()
            new_flag = Flagged(user_id=user_id, reason=reason)
            db.session.add(new_flag)
            db.session.commit()
            flash('User flagged successfully.', 'success')
        elif action == 'unflag':
            Flagged.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            flash('User unflagged successfully.', 'success')
        return redirect(url_for('admin_users'))

    search_query = request.args.get('search', '')

    users = Users.query.filter(Users.username.ilike(f'%{search_query}%')).all()
    user_ids = [user.id for user in users]

    influencers = Influencer.query.join(Users).outerjoin(Flagged, Users.id == Flagged.user_id).filter(
        Users.id.in_(user_ids),
        Users.role == 'Influencer',
        Flagged.user_id == None
    ).all()

    influencer_list = []
    for influencer in influencers:
        user = next((u for u in users if u.id == influencer.user_id), None)
        if user:
            influencer_list.append({
                "id": user.id,
                "username": user.username,
                "password": user.password,
                "name": influencer.name,
                "category": influencer.category,
                "niche": influencer.niche,
                "reach": influencer.reach,
                "platform": influencer.platform,
                "earnings": influencer.earnings
            })

    sponsors = Sponsor.query.join(Users).outerjoin(Flagged, Users.id == Flagged.user_id).filter(
        Users.id.in_(user_ids),
        Users.role == 'Sponsor',
        Flagged.user_id == None
    ).all()

    sponsor_list = []
    for sponsor in sponsors:
        user = next((u for u in users if u.id == sponsor.user_id), None)
        if user:
            sponsor_list.append({
                "id": user.id,
                "username": user.username,
                "password": user.password,
                "company_name": sponsor.company_name,
                "industry": sponsor.industry,
                "budget": sponsor.budget,
            })

    flagged_users = Flagged.query.join(Users).filter(
        Flagged.user_id != None,
        Flagged.campaign_id == None,
        Users.id.in_(user_ids)
    ).all()

    flagged_users_list = []
    for flagged in flagged_users:
        user = next((u for u in users if u.id == flagged.user_id), None)
        if user:
            flagged_users_list.append({
                "user_id": flagged.user_id,
                "username": user.username,
                "reason": flagged.reason,
            })

    return render_template('admin/users.html',
                            influencer_list=influencer_list,
                            sponsor_list=sponsor_list,
                            flagged_users=flagged_users_list)

@app.route('/admin/campaigns', methods = ['GET', 'POST'])
def admin_campaigns():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    ## Handle search functionality
    search_query = request.args.get('search', '')

    ## Filter unflagged campaigns
    campaigns = Campaign.query.outerjoin(Flagged, Campaign.id == Flagged.campaign_id).filter(
        Flagged.campaign_id == None,
        Campaign.name.ilike(f'%{search_query}%') | Campaign.description.ilike(f'%{search_query}%')
    ).all()

    ## Filter flagged campaigns
    flagged_campaigns = Flagged.query.filter(
        Flagged.campaign_id != None,
        Campaign.name.ilike(f'%{search_query}%') | Campaign.description.ilike(f'%{search_query}%')
    ).all()

    if request.method == 'POST':
        ## Handle flag/unflag actions
        campaign_id = request.form.get('campaign_id')
        action = request.form.get('action')
        if action == 'flag':
            reason = request.form.get('reason', 'No reason provided.').strip()
            new_flag = Flagged(campaign_id=campaign_id, reason=reason)
            db.session.add(new_flag)
            db.session.commit()
        elif action == 'unflag':
            Flagged.query.filter_by(campaign_id=campaign_id).delete()
            db.session.commit()
        return redirect(url_for('admin_campaigns'))

    return render_template('admin/campaigns.html', campaigns=campaigns, flagged_campaigns=flagged_campaigns)

'''__________________________________________________________Sponsor_Routes__________________________________________________________'''

@app.route('/sponsor/dashboard', methods = ['GET', 'POST'])
def sponsor_dashboard():
    if 'user_id' not in session or session.get('role') != 'Sponsor':
        flash('Please log in as a sponsor to access this page.', 'error')
        return redirect(url_for('login'))
    
    sponsor_id = session['user_id']
    sponsor = Sponsor.query.filter_by(user_id = sponsor_id).first()
    
    if not sponsor:
        flash('Sponsor not found.', 'error')
        return redirect(url_for('login'))
    
    ## Get all campaigns for the sponsor
    campaigns = Campaign.query.filter_by(sponsor_id = sponsor.user_id).all()
    ad_requests = AdRequest.query.filter_by()
    
    ## Filter running and past campaigns based on end_date
    today = date.today()
    running_campaigns = [campaign for campaign in campaigns if campaign.end_date >= today]
    past_campaigns = [campaign for campaign in campaigns if campaign.end_date < today]
    
    ## Count of campaigns
    campaigns_count = len(campaigns)
    running_campaigns_count = len(running_campaigns)
    past_campaigns_count = len(past_campaigns)
    
    ## Get the reach of each campaign
    campaign_names = [campaign.name for campaign in campaigns]
    ## Get the reach of each campaign
    campaign_reach = [
        db.session.query(db.func.sum(Influencer.reach)).join(AdRequest, Influencer.user_id == AdRequest.influencer_id).filter(
            AdRequest.campaign_id == campaign.id,
            AdRequest.status == 'Accepted'
        ).scalar() or 0
        for campaign in campaigns
    ]

    rusty_red = '#DA2C43'

    plt.clf()
    plt.figure(figsize = (8, 6))
    plt.bar(campaign_names, campaign_reach, color = rusty_red)
    plt.xlabel('Campaign Name')
    plt.ylabel('Total Reach')
    plt.title('Total Reach per Campaign')
    plt.xticks(rotation = 45, ha = 'right')
    plt.tight_layout()
    plt.savefig('static/images/reach_by_campaign.png')
    plt.close()

    return render_template('sponsor/dashboard.html', 
                           sponsor = sponsor, 
                           campaigns_count = campaigns_count,
                           running_campaigns_count = running_campaigns_count,
                           past_campaigns_count = past_campaigns_count,
                           running_campaigns = running_campaigns,
                           past_campaigns = past_campaigns,
                           reach_by_campaign_chart = 'static/images/reach_by_campaign.png')

@app.route('/sponsor/edit_profile', methods = ['GET', 'POST'])
def sponsor_edit_profile():
    if 'user_id' not in session or session['role'] != 'Sponsor':
        flash('Please log in as sponsor to access this page.', 'error')
        return redirect(url_for('login'))
    
    user = Users.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    sponsor = Sponsor.query.filter_by(user_id = user.id).first()
    if not sponsor:
        flash('Sponsor details not found', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password').strip() if request.form.get('password') else None
        company_name = request.form.get('company_name').strip() if request.form.get('company_name') else None
        budget = request.form.get('budget').strip() if request.form.get('budget') else None
        industry = request.form.get('industry').strip() if request.form.get('industry') else None

        ## Validate the new password
        if not any([new_password]):
            flash('Password is required', 'error')
            return render_template('sponsor/edit_profile.html', user = user, sponsor = sponsor)
        
        user.password = new_password
        sponsor.company_name = company_name
        sponsor.budget = budget
        sponsor.industry = industry
        
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('sponsor_edit_profile'))
        
    return render_template('sponsor/edit_profile.html', 
                           user = user, 
                           sponsor = sponsor)

@app.route('/sponsor/create_campaign', methods = ['GET', 'POST'])
def sponsor_create_campaign():
    if 'user_id' not in session or session.get('role') != 'Sponsor':
        flash('Please log in as a sponsor to access this page.', 'error')
        return redirect(url_for('login'))
    
    sponsor_id = session['user_id']
    sponsor = Sponsor.query.filter_by(user_id = sponsor_id).first()
    if not sponsor:
        flash('Sponsor not found.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name').strip()
        description = request.form.get('description').strip()
        start_date = request.form.get('start_date').strip()
        end_date = request.form.get('end_date').strip()
        budget = request.form.get('budget').strip()
        visibility = request.form.get('visibility').strip()
        goals = request.form.get('goals').strip()

        if not all([name, description, start_date, end_date, budget, visibility, goals]):
            flash('All fields are required.', 'error')
            return render_template('sponsor/create_campaign.html')
        
        try:
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
            if end_date_parsed < start_date_parsed:
                flash('End date should be before the sart date.', 'error')
                return render_template('/sponsor/create_campaign.html')
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('sponsor/create_campaign.html')

        existing_campaign = Campaign.query.filter_by(name = name, sponsor_id = sponsor.user_id).first()
        if existing_campaign:
            flash('A campaign with this name already exists.', 'error')
            return render_template('sponsor/create_campaign.html')

        new_campaign = Campaign(sponsor_id = sponsor.user_id, name = name, description = description, start_date = start_date_parsed, 
                                end_date = end_date_parsed, budget = budget, visibility = visibility, goals = goals)
        db.session.add(new_campaign)
        db.session.commit()
        
        flash('Campaign registered successfully!', 'success')
        return redirect(url_for('sponsor_send_request'))
    
    return render_template('sponsor/create_campaign.html')

@app.route('/sponsor/send_request', methods = ['GET', 'POST'])
def sponsor_send_request():
    if 'user_id' not in session or session.get('role') != 'Sponsor':
        flash('Please log in as a sponsor to access this page.', 'error')
        return redirect(url_for('login'))

    sponsor_id = session['user_id']
    sponsor = Sponsor.query.filter_by(user_id = sponsor_id).first()
    if not sponsor:
        flash('Sponsor not found.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        influencer_ids = request.form.getlist('influencer_ids')

        if not campaign_id or not influencer_ids:
            flash('Please select a campaign and at least one influencer.', 'error')
            return redirect(url_for('sponsor_send_request'))

        for influencer_id in influencer_ids:
            influencer = Influencer.query.get(influencer_id)
            messages = request.form.get(f'messages_{influencer_id}').strip()
            requirements = request.form.get(f'requirements_{influencer_id}').strip()
            payment_amount = request.form.get(f'payment_amount_{influencer_id}').strip()
            if not influencer:
                flash(f'Influencer with name {influencer.name} not found.', 'error')
                return redirect(url_for('sponsor_send_request'))
            if not all([messages, requirements, payment_amount]):
                flash('All fields are required.', 'error')
            
            ## Check if the influencer is already added to the campaign
            existing_request = AdRequest.query.filter_by(campaign_id = campaign_id, influencer_id = influencer_id).first()
            if existing_request:
                flash(f'Influencer with name {influencer.name} is already added to this campaign.', 'error')
                return redirect(url_for('sponsor_send_request'))

            ad_request = AdRequest(sponsor_id = sponsor_id, campaign_id = campaign_id, influencer_id = influencer.user_id, messages = messages, 
                                   requirements = requirements, payment_amount = payment_amount, status = 'Pending')
            db.session.add(ad_request)

        db.session.commit()
        flash('Requests sent successfully!', 'success')
        return redirect(url_for('sponsor_send_request'))

    campaigns = Campaign.query.filter_by(sponsor_id = sponsor.user_id).all()
    if not campaigns:
        flash('No campaigns found.', 'error')
        return redirect(url_for('sponsor_send_request'))
    influencers = Influencer.query.filter(Influencer.category == sponsor.industry).all()
    campaign_details = []
    today = datetime.today().date()
    joined_influencers = []
    for campaign in campaigns:
        days_passed = (today - campaign.start_date).days
        total_days = (campaign.end_date - campaign.start_date).days
        progress = (days_passed / total_days) * 100 if total_days > 0 else 0
        if progress >= 100:
            progress = f'Completed on {campaign.end_date}'

        joined_influencers = db.session.query(Influencer.name).join(
            AdRequest, Influencer.user_id == AdRequest.influencer_id
        ).filter(
            AdRequest.campaign_id == campaign.id,
            AdRequest.status == 'Accepted'
        ).all()
        
        campaign_details.append({
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'progress': progress or 0,
            'joined_influencers': [name for name, in joined_influencers] or []
        })

    return render_template('sponsor/send_request.html', 
                           campaigns = campaign_details, 
                           influencers = influencers)

@app.route('/sponsor/manage_requests', methods = ['GET', 'POST'])
def sponsor_manage_requests():
    if 'user_id' not in session or session.get('role') != 'Sponsor':
        flash('Please log in as a sponsor to access this page.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    sponsor = Sponsor.query.filter_by(user_id = user_id).first()
    
    if not sponsor:
        flash('Sponsor not found.', 'error')
        return redirect(url_for('login'))

    sponsor_id = sponsor.user_id  ## Get the sponsor ID

    ## Query all campaigns by the sponsor
    campaigns = Campaign.query.filter_by(sponsor_id = sponsor_id).all()

    ## Query all requests related to the sponsor's campaigns
    campaign_ids = [campaign.id for campaign in campaigns]

    ## Query AdRequests and join with Influencer
    requests = AdRequest.query.join(Influencer, AdRequest.influencer_id == Influencer.user_id)\
                          .filter(AdRequest.campaign_id.in_(campaign_ids))\
                          .add_columns(Influencer.name, Influencer.reach, Influencer.platform)\
                          .all()

    ## Prepare request details for displaying in the template
    request_details = {}
    for campaign in campaigns:
        campaign_requests = [r for r in requests if r[0].campaign_id == campaign.id]
        request_details[campaign.id] = {
            'campaign': campaign,
            'requests': [{'ad_request': r[0], 'influencer_name': r[1], 'influencer_reach': r[2],
                          'influencer_platform': r[3], 
                          } for r in campaign_requests]
        }

    if request.method == 'POST':
        ad_request_id = request.form.get('ad_request_id')
        action = request.form.get('action')
        ad_request = AdRequest.query.get(ad_request_id)
        campaign = Campaign.query.filter(Campaign.id == ad_request.campaign_id).first()
        sponsor = Sponsor.query.filter(Sponsor.user_id == campaign.sponsor_id).first()
        influencer = Influencer.query.filter(Influencer.user_id == ad_request.influencer_id).first()
        
        if action == 'negotiate':
            ad_request.negotiated_amount = float(request.form.get('negotiated_amount').strip())
            ad_request.status = 'Negotiation'
        elif action == 'accept':
            amount = 0
            if ad_request.negotiated_amount:
                amount = ad_request.negotiated_amount
            else: 
                ad_request.payment_amount
            if amount > 0:
                if sponsor.budget >= amount and campaign.budget >= amount:
                    influencer.earnings +=amount
                    campaign.budget -= amount
                    sponsor.budget - amount
                    ad_request.status = 'Accepted'
                else:
                    flash('Insufficient budget', 'error')
                    return redirect(url_for('sponsor_manage_requests'))
            else:
                flash('Payment amount must be greater than zero', 'error')
                return redirect(url_for('sponsor_manage_requests'))
        elif action == 'revoke':
            db.session.delete(ad_request)
        
        db.session.commit()
        flash('Action performed successfully', 'success')
        return redirect(url_for('sponsor_manage_requests'))

    return render_template('sponsor/manage_requests.html', 
                            request_details = request_details)

@app.route('/sponsor/manage_campaigns', methods = ['GET', 'POST'])
def sponsor_manage_campaigns():
    if 'user_id' not in session or session.get('role') != 'Sponsor':
        flash('Please log in as a sponsor to access this page.', 'error')
        return redirect(url_for('login'))

    sponsor_id = session['user_id']
    search_query = request.args.get('search', '')
    if search_query:
        campaigns = Campaign.query.filter(
            Campaign.name.ilike(f'%{search_query}%') |
            Campaign.description.ilike(f'%{search_query}%')
        ).all()
    else:
        campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor_id).all()
    
    campaign_details = []
    joined_influencers = []
    today = datetime.today().date()
    for campaign in campaigns:
        days_passed = (today - campaign.start_date).days
        total_days = (campaign.end_date - campaign.start_date).days
        progress = (days_passed / total_days) * 100 if total_days > 0 else 0
        if progress >= 100:
            progress = f'Completed on {campaign.end_date}'

        joined_influencers = db.session.query(Influencer.name).join(
            AdRequest, Influencer.user_id == AdRequest.influencer_id
        ).filter(
            AdRequest.campaign_id == campaign.id,
            AdRequest.status == 'Accepted'
        ).all()
        campaign_details.append({
            'campaign': campaign,
            'progress': progress or 0,
            'joined_influencers': [name for name, in joined_influencers] or []
        })

    return render_template('sponsor/manage_campaign.html', 
                            campaigns = campaign_details)

@app.route('/sponsor/edit_campaign', methods = ['POST'])
def sponsor_edit_campaign():
    campaign_id = request.form.get('campaign_id')
    campaign = Campaign.query.get(campaign_id)
    if campaign:
        campaign.name = request.form.get('name')
        campaign.description = request.form.get('description').strip()
        campaign.budget = request.form.get('budget').strip()
        campaign.visibility = request.form.get('visibility').strip()
        campaign.goals = request.form.get('goals').strip()
        db.session.commit()
        flash('Campaign updated successfully', 'success')
    else:
        flash('Campaign not found', 'error')
    return redirect(url_for('sponsor_manage_campaigns'))

@app.route('/sponsor/delete_campaign', methods = ['POST'])
def sponsor_delete_campaign():
    campaign_id = request.form.get('campaign_id')
    campaign = Campaign.query.get(campaign_id)
    if campaign:
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully', 'success')
    else:
        flash('Campaign not found', 'error')
    return redirect(url_for('sponsor_manage_campaigns'))

'''__________________________________________________________Influencer_Routes__________________________________________________________'''
@app.route('/influencer/dashboard', methods = ['GET'])
def influencer_dashboard():
    if 'user_id' not in session or session.get('role') != 'Influencer':
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    influencer_id = session['user_id']
    name = Users.query.get(influencer_id).username

    ## Statistics
    requests_count = AdRequest.query.filter(AdRequest.influencer_id == influencer_id).count()
    joined_campaigns_count = AdRequest.query.filter(AdRequest.influencer_id == influencer_id, AdRequest.status == 'Accepted').count()
    earnings = db.session.query(func.sum(AdRequest.payment_amount)).filter(AdRequest.influencer_id == influencer_id, AdRequest.status == 'Accepted').scalar()
        
    ## Generate chart for earnings by campaign
    earnings_by_campaign = db.session.query(AdRequest.payment_amount,Campaign.name).join(Campaign, AdRequest.campaign_id == Campaign.id).filter(AdRequest.influencer_id  == influencer_id, AdRequest.status == 'Accepted').all()

    ## Extract data for plotting
    payment_amounts = [result[0] for result in earnings_by_campaign]
    campaign_names = [result[1] for result in earnings_by_campaign]

    ## Plotting
    bar_width = 0.4
    dartmouth_green = '#00693e'
    plt.clf()
    plt.figure(figsize = (8, 6))
    plt.bar(campaign_names, payment_amounts, bar_width, color = dartmouth_green)
    plt.xlabel('Campaign Name')
    plt.ylabel('Payment Amount')
    plt.title('Payment Amount by Campaign')
    plt.xticks(rotation = 45, ha = 'right')
    plt.tight_layout()
    plt.savefig('static/images/earning_by_campaign.png')

    return render_template('influencer/dashboard.html', name = name,
                           earnings = earnings, 
                           joined_campaigns_count = joined_campaigns_count, 
                           requests_count = requests_count,
                           earning_by_campaign_chart = 'images/earning_by_campaign.png')

@app.route('/influencer/edit_profile', methods = ['GET', 'POST'])
def influencer_edit_profile():
    if 'user_id' not in session or session['role'] != 'Influencer':
        flash('Please log in as influencer to access this page.', 'error')
        return redirect(url_for('login'))
    
    user = Users.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    influencer = Influencer.query.filter_by(user_id = user.id).first()
    if not influencer:
        flash('Influencer details not found', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password').strip()
        new_name = request.form.get('name').strip()
        new_category = request.form.get('category').strip()
        new_niche = request.form.get('niche').strip()
        new_reach = request.form.get('reach').strip()
        new_platform = request.form.get('platform').strip()
        
        ## Validate the form
        if not any([new_password, new_name, new_category, new_niche, new_reach, new_platform]):
            flash('All fields are required', 'error')
            return redirect(url_for('influencer_edit_profile'))
        
        user.password = new_password
        influencer.name = new_name
        influencer.category = new_category
        influencer.niche = new_niche
        influencer.reach = new_reach
        influencer.platform = new_platform
        
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('influencer_edit_profile'))
        
    return render_template('influencer/edit_profile.html', 
                           user = user, 
                           influencer = influencer)

@app.route('/influener/view_campaigns', methods = ['GET'])
def influencer_view_campaigns():
    if 'user_id' not in session or session.get('role') != 'Influencer':
        flash('Please log in as a sponsor to access this page.', 'error')
        return redirect(url_for('login'))

    influencer_id = session['user_id']
    search_query = request.args.get('search', '')
    if search_query:
        campaigns = Campaign.query.filter(
            Campaign.name.ilike(f'%{search_query}%') |
            Campaign.description.ilike(f'%{search_query}%')
        ).all()
    else:
        campaigns = Campaign.query.join(AdRequest, Campaign.id == AdRequest.campaign_id).filter(
            AdRequest.influencer_id == influencer_id,
            AdRequest.status == 'Accepted').all()

    
    campaign_details = []
    joined_influencers = []
    today = datetime.today().date()
    for campaign in campaigns:
        days_passed = (today - campaign.start_date).days
        total_days = (campaign.end_date - campaign.start_date).days
        progress = (days_passed / total_days) * 100 if total_days > 0 else 0
        if progress >= 100:
            progress = f'Completed on {campaign.end_date}'

        joined_influencers = db.session.query(Influencer.name).join(
            AdRequest, Influencer.user_id == AdRequest.influencer_id
        ).filter(
            AdRequest.campaign_id == campaign.id,
            AdRequest.status == 'Accepted'
        ).all()
        campaign_details.append({
            'campaign': campaign,
            'progress': progress or 0,
            'joined_influencers': [name for name, in joined_influencers] or []
        })

    return render_template('influencer/manage_campaign.html', 
                            campaigns = campaign_details)



@app.route('/influencer/ad_requests', methods = ['GET', 'POST'])
def influencer_manage_ad_requests():
    if 'user_id' not in session or session.get('role') != 'Influencer':
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    influencer_id = session.get('user_id')

    search_query = request.args.get('search', '')
    if search_query:
        ad_requests = AdRequest.query.filter(
            AdRequest.influencer_id == influencer_id,
            (Campaign.name.ilike(f'%{search_query}%') |
             AdRequest.status.ilike(f'%{search_query}%'))
        ).join(Campaign, AdRequest.campaign_id == Campaign.id).all()
    else:
        ad_requests = AdRequest.query.filter_by(influencer_id = influencer_id).join(Campaign).all()

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        ad_request = AdRequest.query.get(request_id)
        campaign = Campaign.query.filter(Campaign.id == ad_request.campaign_id).first()
        sponsor = Sponsor.query.filter(Sponsor.user_id == campaign.sponsor_id).first()
        influencer = Influencer.query.filter(Influencer.user_id == ad_request.influencer_id).first()
        if action == 'accept':
            amount = 0
            if ad_request.negotiated_amount:
                amount = ad_request.negotiated_amount
            else: 
                ad_request.payment_amount
            if amount > 0:
                influencer.earnings +=amount
                campaign.budget - amount
                sponsor.budget - amount
                ad_request.status = 'Accepted'
            else:
                flash('Payment amount must be greater than zero', 'error')
                return redirect(url_for('influencer_manage_ad_requests'))
        elif action == 'reject':
            ad_request.status = 'Rejected'
        elif action == 'negotiate':
            payment_amount = float(request.form.get('negotiated_amount').strip())
            ad_request.negotiated_amount = payment_amount
            ad_request.status = 'Negotiation'
        db.session.commit()
        flash('Action performed successfully', 'success')
        return redirect(url_for('influencer_manage_ad_requests'))

    return render_template('influencer/requests.html', 
                           ad_requests = ad_requests)

@app.route('/influencer/search_campaigns', methods = ['GET', 'POST'])
def influencer_search_campaigns():
    if 'user_id' not in session or session.get('role') != 'Influencer':
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')
    query = Campaign.query.filter_by(visibility = 'public')

    if search_query:
        query = query.filter(
            (Campaign.name.ilike(f'%{search_query}%')) |
            (Campaign.description.ilike(f'%{search_query}%'))
        )
    
    campaigns = query.all()
    campaign_details = []

    today = datetime.today().date()
    for campaign in campaigns:
        days_passed = (today - campaign.start_date).days
        total_days = (campaign.end_date - campaign.start_date).days
        progress = (days_passed / total_days) * 100 if total_days > 0 else 0
        if progress >= 100:
            progress = f'Completed on {campaign.end_date}'
        
        campaign_details.append({
            'campaign': campaign,
            'progress': progress
        })

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        payment_amount = request.form.get('payment_amount').strip()
        message = request.form.get('message').strip()
        requirement = request.form.get('requirement').strip()
        sponsor_id = Campaign.query.filter_by(id = campaign_id).first().sponsor_id

        new_ad_request = AdRequest(
            sponsor_id = sponsor_id,
            campaign_id = campaign_id,
            influencer_id = session['user_id'],
            messages = message,
            requirements = requirement,
            payment_amount = payment_amount,
            negotiated_amount = payment_amount,
            status = 'Pending'
        )
        db.session.add(new_ad_request)
        db.session.commit()

        flash('Request to join campaign sent successfully!', 'success')
        return redirect(url_for('influencer_search_campaigns'))

    return render_template('influencer/search_campaigns.html', 
                           campaign_details = campaign_details)

if __name__ == '__main__':
    app.run(debug = True)