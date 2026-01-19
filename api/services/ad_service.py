
from ..firebase_setup import get_db
from firebase_admin import firestore
from datetime import datetime
from . import wallet_service

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
        'createdAt': datetime.now().isoformat(),
        'active': True,
        'viewCount': 0
    }
    
    ad_ref.set(new_ad)
    return new_ad

def fetch_ads(user_id=None):
    db = get_db()
    # In JS: .where('active', '==', true).limit(20)
    query = db.collection('ads').where('active', '==', True).limit(20)
    docs = query.stream()
    
    ads = []
    for doc in docs:
        ads.append(doc.to_dict())
    return ads

def mark_ad_complete(user_id, ad_id):
    db = get_db()
    
    if not ad_id:
        raise Exception('Invalid adId')
        
    # Check if user has already viewed this ad (outside transaction for speed/fail-fast)
    existing_view_query = db.collection('ad_views')\
        .where('userId', '==', user_id)\
        .where('adId', '==', ad_id)\
        .limit(1).stream()
        
    # stream() returns a generator, check if empty
    if any(existing_view_query):
        raise Exception('Reward already claimed for this advertisement')
        
    ad_ref = db.collection('ads').document(ad_id)
    
    @firestore.transactional
    def complete_transaction(transaction):
        ad_snapshot = transaction.get(ad_ref)
        if not ad_snapshot.exists:
             raise Exception('Ad not found')
             
        ad_data = ad_snapshot.to_dict()
        reward = ad_data.get('pointReward', 0)
        
        # Double check view in transaction
        view_check_query = db.collection('ad_views')\
            .where('userId', '==', user_id)\
            .where('adId', '==', ad_id)\
            .limit(1)
            
        # Transactional queries in python admin sdk require passing transaction to the query execution if possible?
        # Alternatively, we stream and it might not be fully transactional if query doesn't support passing transaction.
        # Actually, Firestore queries in transactions are tricky. 
        # But typically we can just run the query. 
        # However, to be safe and lock-free correct, creating the view doc with a deterministic ID (e.g. userId_adId) is better, 
        # but the JS code didn't do that, it queried.
        # We will assume the check at start is enough for common case, and let's try to query inside if allowed.
        # Re-implementing strictly:
        
        # Note: google-cloud-firestore generic client allows passing transaction=transaction to get()
        view_check_docs = list(view_check_query.stream(transaction=transaction))
        if view_check_docs:
             raise Exception('Reward already claimed')
             
        # Save view
        view_ref = db.collection('ad_views').document()
        transaction.set(view_ref, {
            'userId': user_id,
            'adId': ad_id,
            'timestamp': datetime.now().isoformat(),
            'reward': reward
        })
        
        # Increment view count
        transaction.update(ad_ref, {
            'viewCount': firestore.Increment(1)
        })
        
        # We need to call add_points but add_points is ALSO a transaction.
        # Nested transactions are not supported elegantly by just calling function.
        # We must inline the wallet logic or refactor.
        # JS code: db.runTransaction(async (t) => { ... walletService.addPoints ... })
        # BUT walletService.addPoints uses db.runTransaction in JS?
        # Wait, looking at JS code:
        # exports.markAdComplete = ... db.runTransaction(async (t) => { ... const newBalance = await walletService.addPoints(..., t) ... })
        # Actually in JS code shown:
        # exports.markAdComplete calls walletService.addPoints inside transaction t?
        # Let's check JS file again. 
        # JS implementation of addPoints: 
        # exports.addPoints = async (userId, amount, description) => { return await db.runTransaction(...) }
        # The JS implementation calls `walletService.addPoints` INSIDE the transaction callback.
        # `walletService.addPoints` starts a NEW transaction `db.runTransaction`.
        # Firestore libraries usually don't support nested transactions.
        # If the JS code works, maybe `addPoints` wasn't creating a NEW transaction or the library handles it?
        # Wait, read `adController.js`:
        # 94:         const newBalance = await walletService.addPoints(
        # 95:             userId,
        # 96:             reward,
        # 97:             `Watched Ad: ${adData.title}`
        # 98:         );
        # This implementation in `adController.js` is calling `walletService` which does a transaction.
        # But `markAdComplete` runs a transaction. 
        # The JS file I read for `adService.js` line 94 calls `walletService.addPoints`.
        # Unless `walletService.addPoints` logic is duplicated or handles being passed a transaction?
        # In `walletService.js`, `addPoints` creates a transaction.
        # So in JS this might be buggy or running two separate transactions (which is bad for atomicity but technically possible if `addPoints` is awaited).
        # Actually, `markAdComplete` awaits `walletService.addPoints`.
        # But `markAdComplete` is inside a transaction. 
        # Accessing Firestore inside a transaction requires using the transaction object for reads.
        # If `addPoints` runs a separate transaction, it might deadlock or just be separate.
        # To be SAFE and strictly ATOMIC in Python: I will INLINE the wallet update logic here.
        
        user_ref = db.collection('users').document(user_id)
        user_snapshot = transaction.get(user_ref)
        if not user_snapshot.exists:
             raise Exception('User does not exist')
             
        current_balance = user_snapshot.to_dict().get('walletBalance', 0)
        new_balance = current_balance + reward
        
        transaction.update(user_ref, {'walletBalance': new_balance})
        
        txn_ref = db.collection('transactions').document()
        transaction.set(txn_ref, {
            'userId': user_id,
            'amount': reward,
            'type': 'credit',
            'description': f"Watched Ad: {ad_data.get('title')}",
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'success': True,
            'reward': reward,
            'newBalance': new_balance
        }

    transaction = db.transaction()
    return complete_transaction(transaction)

def get_dashboard_stats():
    db = get_db()
    # Note: .get() retrieves all documents. Expensive but matches JS.
    ads_snapshot = db.collection('ads').get()
    views_snapshot = db.collection('ad_views').get()
    users_snapshot = db.collection('users').get()
    
    total_ads = len(ads_snapshot)
    total_views = len(views_snapshot)
    total_users = len(users_snapshot)
    
    total_earnings = 0
    views_by_day_map = {
        'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0
    }
    
    for doc in views_snapshot:
        data = doc.to_dict()
        total_earnings += data.get('reward', 0)
        
        ts = data.get('timestamp')
        if ts:
             try:
                # Handle ISO format
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                day_name = dt.strftime('%a') # Mon, Tue...
                if day_name in views_by_day_map:
                    views_by_day_map[day_name] += 1
             except:
                 pass
                 
    # Convert map back to list to match JS structure
    views_by_day = [{'day': k, 'views': v} for k, v in views_by_day_map.items()]
    # actually JS uses specific order Mon-Sun
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    views_by_day_ordered = [{'day': d, 'views': views_by_day_map.get(d, 0)} for d in days_order]

    active_campaigns = sum(1 for doc in ads_snapshot if doc.to_dict().get('active'))

    return {
        'totalAds': total_ads,
        'totalViews': total_views,
        'totalUsers': total_users,
        'totalEarnings': total_earnings,
        'activeCampaigns': active_campaigns,
        'viewsByDay': views_by_day_ordered
    }
