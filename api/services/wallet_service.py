from ..firebase_setup import get_db
from firebase_admin import firestore


def get_balance(user_id):
    if not user_id:
        raise Exception("User ID required")

    db = get_db()
    user_doc = db.collection('users').document(user_id).get()

    if not user_doc.exists:
        return 0

    return user_doc.to_dict().get('walletBalance', 0)


# ----------------------------------------
# Add Points (Credit)
# ----------------------------------------
def add_points(user_id, amount, description):

    if not user_id:
        raise Exception("User ID required")

    if amount is None or amount <= 0:
        raise Exception("Invalid amount")

    db = get_db()
    user_ref = db.collection('users').document(user_id)

    @firestore.transactional
    def update_in_transaction(transaction):

        snapshot = transaction.get(user_ref)
        if not snapshot.exists:
            raise Exception('User does not exist')

        current_balance = snapshot.to_dict().get('walletBalance', 0)
        new_balance = current_balance + amount

        transaction.update(user_ref, {
            'walletBalance': new_balance
        })

        txn_ref = db.collection('transactions').document()
        transaction.set(txn_ref, {
            'userId': user_id,
            'amount': amount,
            'type': 'credit',
            'description': description,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return new_balance

    transaction = db.transaction()
    return update_in_transaction(transaction)


# ----------------------------------------
# Redeem Points (Debit)
# ----------------------------------------
def redeem_points(user_id, amount, payment_method, payment_details):

    if not user_id:
        raise Exception("User ID required")

    if amount is None or amount <= 0:
        raise Exception("Invalid amount")

    if not payment_method:
        raise Exception("Payment method required")

    db = get_db()
    user_ref = db.collection('users').document(user_id)

    @firestore.transactional
    def redeem_in_transaction(transaction):

        snapshot = transaction.get(user_ref)
        if not snapshot.exists:
            raise Exception('User does not exist')

        current_balance = snapshot.to_dict().get('walletBalance', 0)

        if current_balance < amount:
            raise Exception('Insufficient balance')

        new_balance = current_balance - amount

        transaction.update(user_ref, {
            'walletBalance': new_balance
        })

        request_ref = db.collection('redemption_requests').document()
        transaction.set(request_ref, {
            'userId': user_id,
            'amount': amount,
            'paymentMethod': payment_method,
            'paymentDetails': payment_details,
            'status': 'pending',
            'createdAt': firestore.SERVER_TIMESTAMP
        })

        txn_ref = db.collection('transactions').document()
        transaction.set(txn_ref, {
            'userId': user_id,
            'amount': -amount,
            'type': 'debit',
            'description': 'Redemption Request',
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return {
            'success': True,
            'newBalance': new_balance,
            'message': 'Redemption request submitted'
        }

    transaction = db.transaction()
    return redeem_in_transaction(transaction)
