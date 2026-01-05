from flask import Flask, render_template, request, jsonify, session, redirect
from forms import CarbonFootprintForm
from utils import (get_personalized_suggestions, calculate_tree_equivalent, get_badge_details,
                  create_emissions_chart, create_comparison_chart, get_achievement_stats)

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = 'AIzaSyDtj4fVBSHa4s6WdVupOoegQBCAzQ-XQwY'  # Change this to a secure secret key in production

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CarbonFootprintForm()
    if request.method == 'POST':
        # Store form data in session
        session['form_data'] = request.form
        return jsonify({
            'success': True,
            'redirect': '/results'
        })
    return render_template('index.html', form=form)

@app.route('/results')
def results():
    if 'form_data' not in session:
        return redirect('/')
    
    form_data = session['form_data']
    
    # Calculate carbon footprint
    total_emissions = calculate_emissions(form_data)
    
    # Get personalized suggestions
    suggestions = get_personalized_suggestions(form_data)
    
    # Calculate environmental equivalents
    impact_equivalents = calculate_tree_equivalent(total_emissions['total'])
    
    # Get badge and achievements
    badge_info = get_badge_details(total_emissions['total'])
    achievements = get_achievement_stats(total_emissions)
    
    # Create visualization charts
    emissions_chart = create_emissions_chart(total_emissions)
    comparison_chart = create_comparison_chart(
        total_emissions['total'],
        12.0  # Average CO2 emissions per person (you can adjust this based on location)
    )
    
    return render_template('results.html',
                         emissions=total_emissions,
                         suggestions=suggestions,
                         badge_info=badge_info,
                         impact_equivalents=impact_equivalents,
                         achievements=achievements,
                         emissions_chart=emissions_chart,
                         comparison_chart=comparison_chart)

def calculate_emissions(data):
    """Calculate carbon emissions based on form data"""
    emissions = {
        'transportation': 0,
        'household': 0,
        'food': 0,
        'waste': 0,
        'lifestyle': 0,
        'total': 0
    }
    
    # Transport emissions
    transport_mode = data.get('transport_mode')
    daily_travel = float(data.get('daily_travel', 0))
    domestic_flights = int(data.get('domestic_flights', 0))
    international_flights = int(data.get('international_flights', 0))
    vehicle_fuel = data.get('vehicle_fuel')
    
    # Base transport emissions
    if transport_mode == 'car':
        base_emission = 0.2  # kg CO2 per km
        if vehicle_fuel == 'diesel':
            base_emission = 0.25
        elif vehicle_fuel == 'electric':
            base_emission = 0.05
        elif vehicle_fuel == 'cng':
            base_emission = 0.15
        emissions['transportation'] += daily_travel * base_emission * 365
    elif transport_mode == 'bike':
        emissions['transportation'] += daily_travel * 0.1 * 365
    elif transport_mode == 'bus':
        emissions['transportation'] += daily_travel * 0.08 * 365
    
    emissions['transportation'] += domestic_flights * 90  # 90 kg per flight
    emissions['transportation'] += international_flights * 200  # 200 kg per flight
    
    # Household emissions
    monthly_electricity = float(data.get('monthly_electricity', 0))
    household_members = int(data.get('household_members', 1))
    ac_usage = data.get('ac_usage')
    home_type = data.get('home_type')
    water_usage = data.get('water_usage')
    
    # Base electricity emissions (0.85 kg CO2 per kWh)
    base_electricity = (monthly_electricity / 8) * 0.85 * 12 / household_members
    
    # Adjust for AC usage
    ac_multiplier = {
        'no': 1.0,
        'seasonal': 1.2,
        'moderate': 1.4,
        'heavy': 1.6
    }.get(ac_usage, 1.0)
    
    # Adjust for home type
    home_multiplier = {
        'apartment1': 1.0,
        'apartment2': 1.2,
        'house': 1.4,
        'villa': 1.6
    }.get(home_type, 1.0)
    
    emissions['household'] = base_electricity * ac_multiplier * home_multiplier
    
    # Food emissions
    diet_type = data.get('diet_type')
    red_meat = data.get('red_meat')
    dairy = data.get('dairy')
    food_waste = data.get('food_waste')
    
    # Base food emissions
    base_food = {
        'non-vegetarian': 2.5,
        'vegetarian': 1.5,
        'vegan': 1.1,
        'eggetarian': 1.7
    }.get(diet_type, 1.5) * 365
    
    # Adjust for red meat consumption
    meat_multiplier = {
        'never': 1.0,
        'occasional': 1.2,
        'weekly': 1.4,
        'frequent': 1.6
    }.get(red_meat, 1.0)
    
    # Adjust for dairy consumption
    dairy_multiplier = {
        'never': 1.0,
        'rarely': 1.1,
        'occasional': 1.2,
        'daily': 1.3
    }.get(dairy, 1.0)
    
    # Adjust for food waste
    waste_multiplier = {
        'never': 1.0,
        'rarely': 1.1,
        'sometimes': 1.2,
        'often': 1.3
    }.get(food_waste, 1.0)
    
    emissions['food'] = base_food * meat_multiplier * dairy_multiplier * waste_multiplier
    
    # Waste emissions
    weekly_waste = data.get('weekly_waste')
    recycling = data.get('recycling')
    waste_segregation = data.get('waste_segregation')
    
    # Base waste emissions
    base_waste = {
        'low': 100,
        'medium': 200,
        'high': 400,
        'very_high': 600
    }.get(weekly_waste, 200)
    
    # Adjust for recycling and segregation
    if recycling == 'all':
        base_waste *= 0.6
    elif recycling == 'some':
        base_waste *= 0.8
    
    if waste_segregation == 'yes':
        base_waste *= 0.9
    
    emissions['waste'] = base_waste
    
    # Lifestyle emissions
    yearly_clothes = data.get('yearly_clothes')
    electronics = data.get('electronics')
    online_shopping = data.get('online_shopping')
    
    # Shopping emissions
    clothes_emissions = {
        'minimal': 100,
        'moderate': 200,
        'frequent': 400,
        'excessive': 600
    }.get(yearly_clothes, 200)
    
    electronics_emissions = {
        'none': 0,
        'low': 100,
        'medium': 200,
        'high': 400
    }.get(electronics, 100)
    
    shopping_frequency = {
        'rarely': 50,
        'monthly': 100,
        'weekly': 200,
        'daily': 400
    }.get(online_shopping, 100)
    
    emissions['lifestyle'] = clothes_emissions + electronics_emissions + shopping_frequency
    
    # Calculate total
    emissions['total'] = sum(value for key, value in emissions.items() if key != 'total')
    
    return emissions

def generate_suggestions(emissions):
    # Placeholder for suggestion generation
    return [
        "Switch to LED bulbs to reduce your household energy consumption",
        "Consider carpooling or using public transport twice a week",
        "Start composting your food waste to reduce methane emissions"
    ]

def assign_badge(emissions):
    total = emissions['total']
    if total < 5:
        return "🌍 Planet Guardian"
    elif total < 10:
        return "🍃 Conscious Consumer"
    else:
        return "🌱 Eco Starter"

if __name__ == '__main__':
    app.run(debug=True)
