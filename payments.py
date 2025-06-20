# Sistema de Pagamentos Stripe Integration
# Para monetização real do GPAS 2.0

from flask import Blueprint, request, jsonify, redirect
import stripe
import os
from datetime import datetime, timedelta
import json

# Configuração do Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')  # Usar chave real em produção
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')

# Blueprint para pagamentos
payments_bp = Blueprint('payments', __name__)

# Planos de preços
PRICING_PLANS = {
    'starter': {
        'name': 'Starter',
        'price_monthly': 19,
        'price_annual': 13,
        'stripe_price_id_monthly': 'price_starter_monthly',
        'stripe_price_id_annual': 'price_starter_annual',
        'features': [
            '100 pesquisas/dia',
            '3 marketplaces',
            'IA básica',
            'Suporte email'
        ]
    },
    'professional': {
        'name': 'Professional',
        'price_monthly': 49,
        'price_annual': 34,
        'stripe_price_id_monthly': 'price_professional_monthly',
        'stripe_price_id_annual': 'price_professional_annual',
        'features': [
            'Pesquisas ilimitadas',
            '15+ marketplaces',
            'IA avançada completa',
            'Automação total',
            'Comandos por voz',
            'Suporte prioritário'
        ]
    },
    'enterprise': {
        'name': 'Enterprise',
        'price_monthly': 99,
        'price_annual': 69,
        'stripe_price_id_monthly': 'price_enterprise_monthly',
        'stripe_price_id_annual': 'price_enterprise_annual',
        'features': [
            'Tudo do Professional',
            'API access',
            'White-label',
            'Utilizadores ilimitados',
            'Suporte dedicado'
        ]
    }
}

@payments_bp.route('/api/payments/config', methods=['GET'])
def get_stripe_config():
    """Retorna configuração pública do Stripe"""
    return jsonify({
        'publishable_key': STRIPE_PUBLISHABLE_KEY,
        'plans': PRICING_PLANS
    })

@payments_bp.route('/api/payments/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Cria sessão de checkout do Stripe"""
    try:
        data = request.get_json()
        plan = data.get('plan')
        billing = data.get('billing', 'monthly')  # monthly ou annual
        
        if plan not in PRICING_PLANS:
            return jsonify({'error': 'Plano inválido'}), 400
        
        plan_data = PRICING_PLANS[plan]
        price_id = plan_data[f'stripe_price_id_{billing}']
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cancel',
            metadata={
                'plan': plan,
                'billing': billing
            }
        )
        
        return jsonify({
            'checkout_session_id': checkout_session.id,
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/api/payments/webhook', methods=['POST'])
def stripe_webhook():
    """Webhook para eventos do Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Processar eventos
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_subscription_renewal(invoice)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)
    
    return jsonify({'status': 'success'})

def handle_successful_payment(session):
    """Processa pagamento bem-sucedido"""
    customer_email = session.get('customer_details', {}).get('email')
    plan = session.get('metadata', {}).get('plan')
    billing = session.get('metadata', {}).get('billing')
    
    # Atualizar utilizador na base de dados
    # (implementar lógica de atualização do plano do utilizador)
    
    print(f"Pagamento bem-sucedido: {customer_email} - Plano: {plan} ({billing})")

def handle_subscription_renewal(invoice):
    """Processa renovação de subscrição"""
    customer_id = invoice.get('customer')
    amount_paid = invoice.get('amount_paid') / 100  # Converter de centavos
    
    print(f"Subscrição renovada: Cliente {customer_id} - €{amount_paid}")

def handle_subscription_cancelled(subscription):
    """Processa cancelamento de subscrição"""
    customer_id = subscription.get('customer')
    
    # Downgrade utilizador para plano gratuito
    print(f"Subscrição cancelada: Cliente {customer_id}")

# Páginas de sucesso e cancelamento
@payments_bp.route('/success')
def payment_success():
    """Página de sucesso após pagamento"""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Pagamento Realizado com Sucesso!</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f9ff; }}
                    .success-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .success-icon {{ font-size: 4rem; color: #10b981; margin-bottom: 20px; }}
                    h1 {{ color: #1f2937; margin-bottom: 20px; }}
                    p {{ color: #6b7280; font-size: 18px; line-height: 1.6; }}
                    .btn {{ background: #6366f1; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }}
                    .btn:hover {{ background: #4f46e5; }}
                </style>
            </head>
            <body>
                <div class="success-container">
                    <div class="success-icon">🎉</div>
                    <h1>Pagamento Realizado com Sucesso!</h1>
                    <p>Obrigado por te juntares ao GPAS 2.0! A tua subscrição está ativa e podes começar a gerar receita imediatamente.</p>
                    <p><strong>Próximos passos:</strong></p>
                    <p>1. Acede ao teu dashboard<br>
                    2. Configura os teus marketplaces preferidos<br>
                    3. Deixa a IA encontrar oportunidades para ti</p>
                    <a href="/dashboard.html" class="btn">Ir para Dashboard</a>
                </div>
                <script>
                    // Tracking de conversão
                    if (typeof gtag !== 'undefined') {{
                        gtag('event', 'purchase', {{
                            'transaction_id': '{session_id}',
                            'value': {session.amount_total / 100},
                            'currency': 'EUR'
                        }});
                    }}
                </script>
            </body>
            </html>
            """
        except Exception as e:
            return f"Erro ao verificar pagamento: {e}", 500
    
    return "Sessão inválida", 400

@payments_bp.route('/cancel')
def payment_cancel():
    """Página de cancelamento"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pagamento Cancelado</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #fef2f2; }
            .cancel-container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .cancel-icon { font-size: 4rem; color: #ef4444; margin-bottom: 20px; }
            h1 { color: #1f2937; margin-bottom: 20px; }
            p { color: #6b7280; font-size: 18px; line-height: 1.6; }
            .btn { background: #6366f1; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }
            .btn:hover { background: #4f46e5; }
        </style>
    </head>
    <body>
        <div class="cancel-container">
            <div class="cancel-icon">😔</div>
            <h1>Pagamento Cancelado</h1>
            <p>Não há problema! Podes sempre voltar quando estiveres pronto para começar a gerar receita com o GPAS 2.0.</p>
            <p>Lembra-te: cada dia que esperas é dinheiro que deixas na mesa.</p>
            <a href="/" class="btn">Voltar ao Site</a>
        </div>
    </body>
    </html>
    """

# Função para registar o blueprint
def register_payments(app):
    """Regista funcionalidades de pagamento na app"""
    app.register_blueprint(payments_bp)
    return app

