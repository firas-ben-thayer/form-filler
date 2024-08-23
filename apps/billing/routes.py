# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, url_for, current_app, request, abort, redirect, jsonify
from apps.billing import blueprint
from flask_login import login_required, current_user
import stripe
from apps.authentication.models import UsedSessionId
from apps import db

@blueprint.route('/billing')
@login_required
def billing():
    return render_template('billing/billing.html')

@blueprint.route('/proposal_charges_empty')
@login_required
def proposal_charges_empty():
    return render_template('billing/proposal_charges_empty.html')

@blueprint.route('/free_plan', methods=['GET','POST'])
@login_required
def free_plan():
    user = current_user
    if user.free_plan_used == False:
        user.free_plan_used = True
        user.subscription_type = 1
        user.reset_proposals()
        db.session.commit()
        return render_template('billing/success.html')
    else:
        return render_template('billing/free_plan_used.html')
        
@blueprint.route('/stripe_pay')
@login_required
def stripe_pay():
    session_20 = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1PpsvzRs0zWjhr4tvYHKwa7Y',
            'quantity': 1,
        }],
        mode='subscription',
        success_url=url_for('billing_blueprint.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('home_blueprint.index', _external=True),
    )
    session_50 = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1PpxdORs0zWjhr4tmvMg1XLO',
            'quantity': 1,
        }],
        mode='subscription',
        success_url=url_for('billing_blueprint.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('home_blueprint.index', _external=True),
    )
    return {
        'checkout_session_20_id': session_20['id'],
        'checkout_session_50_id': session_50['id'],
        'checkout_public_key': current_app.config['STRIPE_PUBLIC_KEY']
    }

@blueprint.route('/success')
@login_required
def success():
    # Get the session_id from the query parameters
    session_id = request.args.get('session_id')
    
    if not session_id:
        return render_template('home/page-403.html'), 403
        
    if UsedSessionId.query.filter_by(session_id=session_id).first():
        return render_template('home/page-403.html'), 403
    
    # Retrieve the session from Stripe
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        return render_template('home/page-403.html'), 403
    
    # Retrieve the subscription information from Stripe
    subscription_id = session.get('subscription')
    if not subscription_id:
        return render_template('home/page-403.html'), 403
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
    except stripe.error.StripeError as e:
        return render_template('home/page-403.html'), 403
    
    price_id = subscription['items']['data'][0]['price']['id']
    
    # Determine the user from the customer_id
    if current_user:
        if price_id == 'price_1PpsvzRs0zWjhr4tvYHKwa7Y':  # $20 Plan
            current_user.subscription_type = 2
        elif price_id == 'price_1PpxdORs0zWjhr4tmvMg1XLO':  # $50 Plan
            current_user.subscription_type = 3

        # Reset the user's proposals based on the new subscription
        current_user.reset_proposals()
        transaction_history_entry = UsedSessionId(session_id = session_id)
        db.session.add(transaction_history_entry)
        
        # Save changes to the database
        db.session.commit()
        return render_template('billing/success.html')
    else:
        return render_template('home/page-403.html'), 403

@blueprint.route('/stripe_webhook', methods=['POST'])
@login_required
def stripe_webhook():
    print('WEBHOOK CALLED')

    if request.content_length > 1024 * 1024:
        print('REQUEST TOO BIG')
        abort(400)
    payload = request.get_data()
    sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = 'whsec_10816af655957f0f050822aa95560bd1f1d3d019a6b60d4eac51f1818439c3cc'
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print('WEBHOOK EVENT CONSTRUCTED:', event)
        
    except ValueError as e:
        # Invalid payload
        print('INVALID PAYLOAD:', str(e))
        return jsonify({'error': 'Invalid payload'}), 400
    
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print('INVALID SIGNATURE:', str(e))
        return jsonify({'error': 'Invalid signature'}), 400
        
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(session)
        line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)
        print(line_items['data'][0]['description'])
    else:
        print("User not found.")

    return jsonify({'status': 'success'}), 200