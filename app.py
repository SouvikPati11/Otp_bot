import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import time
from datetime import datetime
from database import init_db, db_session
from models import User, Order
from services import FiveSimService

load_dotenv()

app = Flask(__name__)
CORS(app)
init_db()

# Initialize 5sim service
five_sim = FiveSimService(api_key=os.getenv('FIVE_SIM_API_KEY'))

@app.route('/api/user/balance', methods=['GET'])
def get_balance():
    # In a real app, you'd get user ID from Telegram WebApp data
    user = User.query.first() or User(balance=0, currency='USD')
    
    # Get actual balance from 5sim
    try:
        profile = five_sim.get_user_profile()
        user.balance = profile['balance']
        user.currency = profile['currency']
        db_session.commit()
    except Exception as e:
        print(f"Error updating balance: {e}")
    
    return jsonify({
        'balance': user.balance,
        'currency': user.currency
    })

@app.route('/api/user/history', methods=['GET'])
def get_history():
    # Get user's order history
    orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return jsonify([{
        'date': order.created_at.isoformat(),
        'service': order.service,
        'number': order.phone,
        'status': order.status
    } for order in orders])

@app.route('/api/buy', methods=['POST'])
def buy_number():
    data = request.json
    country = data.get('country', 'india')
    service = data.get('service', 'instagram')
    
    try:
        # Purchase number from 5sim
        order_data = five_sim.buy_number(country, service)
        
        # Save order to database
        order = Order(
            order_id=order_data['id'],
            phone=order_data['phone'],
            country=country,
            service=service,
            price=order_data['price'],
            status='pending'
        )
        db_session.add(order)
        db_session.commit()
        
        return jsonify({
            'orderId': order_data['id'],
            'phone': order_data['phone'],
            'country': country,
            'service': service,
            'price': order_data['price']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/check/<order_id>', methods=['GET'])
def check_otp(order_id):
    try:
        # Check order status with 5sim
        order_data = five_sim.check_order(order_id)
        
        if order_data.get('sms'):
            # Update order status
            order = Order.query.filter_by(order_id=order_id).first()
            if order:
                order.status = 'success'
                order.sms = order_data['sms'][0]['code']
                order.updated_at = datetime.utcnow()
                db_session.commit()
            
            return jsonify({'otp': order_data['sms'][0]['code']})
        else:
            return jsonify({'otp': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cancel/<order_id>', methods=['POST'])
def cancel_order(order_id):
    try:
        # Cancel order with 5sim
        five_sim.cancel_order(order_id)
        
        # Update order status
        order = Order.query.filter_by(order_id=order_id).first()
        if order:
            order.status = 'cancelled'
            order.updated_at = datetime.utcnow()
            db_session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    app.run(debug=True)
