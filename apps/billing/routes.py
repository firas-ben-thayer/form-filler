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
from apps.authentication.models import Users
import os

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
    user = current_user

    if not user.stripe_customer_id:
        # Create a new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={"user_id": user.id}
        )
        user.stripe_customer_id = customer['id']
        db.session.commit()

    # Create checkout sessions for each plan
    session_8 = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price':  os.environ.get('SESSION_8'),
            'quantity': 1,
        }],
        mode='subscription',
        success_url=url_for('billing_blueprint.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('home_blueprint.index', _external=True),
    )

    session_20 = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price':  os.environ.get('SESSION_20'),
            'quantity': 1,
        }],
        mode='subscription',
        success_url=url_for('billing_blueprint.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('home_blueprint.index', _external=True),
    )

    return {
        'checkout_session_8_id': session_8['id'],
        'checkout_session_20_id': session_20['id'],
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
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config['STRIPE_ENDPOINT_SECRET']

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        print("Invoice object:", invoice)
        subscription_id = invoice['subscription']
        print("Subscription ID:", subscription_id)
        
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            customer_id = subscription['customer']

            # Find the user by their Stripe customer ID
            user = Users.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                user.reset_proposals()  # Reset the proposals based on the subscription type
                db.session.commit()
                
        else:
            print("No subscription ID found in the invoice")

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        subscription_id = invoice['subscription']
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription['customer']

        # Find the user by their Stripe customer ID
        user = Users.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            # Notify user or take some action (e.g., send an email)
            # You can also suspend the user account if needed
            print(f"Payment failed for user {user.email}")

    # Handle other relevant webhook events here

    return jsonify({'status': 'success'}), 200
