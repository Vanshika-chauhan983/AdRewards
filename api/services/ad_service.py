from ..firebase_setup import get_db
from firebase_admin import firestore
from datetime import datetime, timezone

# ----------------------------------------
# Create Ad
# ----------------------------------------
def create_ad(ad_data):
    db = get_db()
    ad_ref = db.collection('ads').document()

    new_ad = {
        'id': ad_ref.id,
        'title': ad_data.get('title'),
        'description': ad_data.get('description'),
        'mediaUrl': ad_data.get('mediaUrl'),
        'mediaType': ad_data.get('mediaType'),
        'pointReward': ad_data.get('pointReward'),
        'timerDuration': ad_data.get('timerDuration', 15),
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'active': True,
        'viewCount': 0
    }

    ad_ref.set(new_ad)
    return new_ad


# ----------------------------------------
# Fetch Ads
# ----------------------------------------
def fetch_ads(user_id=None):
    db = get_db()

    query = db.collection('ads') \
        .where('active', '==', True) \
        .limit(20)

    docs = query.stream()

    return [doc.to_dict() for doc in docs]


# ----------------------------------------
# Mark Ad Complete (Atomic + Safe)
# ----------------------------------------
def mark_ad_complete(user_id, ad_id):
    db = get_db()

    if not ad_id:
        raise Exception('Invalid adId')

    ad_ref = db.collection('ads').document(ad_id)

    # Deterministic view document (prevents duplicate rewards safely)
    view_ref = db.collection('ad_views').document(f"{user_id}_{ad_id}")

    user_ref = db.collection('users').document(user_id)

    @firestore.transactional
    def complete_transaction(transaction):

        # Get ad
        ad_snapshot = transaction.get(ad_ref)
        if not ad_snapshot.exists:
            raise Exception('Ad not found')

        ad_data = ad_snapshot.to_dict()
        reward = ad_data.get('pointReward', 0)

        # Check if reward already claimed (atomic)
        view_snapshot = transaction.get(view_ref)
        if view_snapshot.exists:
            raise Exception('Reward already claimed')

        # Create view record
        transaction.set(view_ref, {
            'userId': user_id,
            'adId': ad_id,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'reward': reward
        })

        # Increment ad view count
        transaction.update(ad_ref, {
            'viewCount': firestore.Increment(1)
        })

        # Update user wallet
        user_snapshot = transaction.get(user_ref)
        if not user_snapshot.exists:
            raise Exception('User does not exist')

        current_balance = user_snapshot.to_dict().get('walletBalance', 0)
        new_balance = current_balance + reward

        transaction.update(user_ref, {
            'walletBalance': new_balance
        })

        # Add transaction record
        txn_ref = db.collection('transactions').document()
        transaction.set(txn_ref, {
            'userId': user_id,
            'amount': reward,
            'type': 'credit',
            'description': f"Watched Ad: {ad_data.get('title')}",
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return {
            'success': True,
            'reward': reward,
            'newBalance': new_balance
        }

    transaction = db.transaction()
    return complete_transaction(transaction)


# ----------------------------------------
# Dashboard Stats
# ----------------------------------------
def get_dashboard_stats():
    db = get_db()

    ads_snapshot = db.collection('ads').get()
    views_snapshot = db.collection('ad_views').get()
    users_snapshot = db.collection('users').get()

    total_ads = len(ads_snapshot)
    total_views = len(views_snapshot)
    total_users = len(users_snapshot)

    total_earnings = 0
    views_by_day_map = {
        'Mon': 0, 'Tue': 0, 'Wed': 0,
        'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0
    }

    for doc in views_snapshot:
        data = doc.to_dict()
        total_earnings += data.get('reward', 0)

        ts = data.get('timestamp')

        if ts:
            try:
                # Firestore Timestamp object handling
                if hasattr(ts, 'to_datetime'):
                    dt = ts.to_datetime()
                else:
                    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))

                day_name = dt.strftime('%a')
                if day_name in views_by_day_map:
                    views_by_day_map[day_name] += 1
            except:
                pass

    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    views_by_day_ordered = [
        {'day': d, 'views': views_by_day_map.get(d, 0)}
        for d in days_order
    ]

    active_campaigns = sum(
        1 for doc in ads_snapshot
        if doc.to_dict().get('active')
    )

    return {
        'totalAds': total_ads,
        'totalViews': total_views,
        'totalUsers': total_users,
        'totalEarnings': total_earnings,
        'activeCampaigns': active_campaigns,
        'viewsByDay': views_by_day_ordered
    }
