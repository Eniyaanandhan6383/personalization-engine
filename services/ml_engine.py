from database import SessionLocal
from models.models import BehaviorLog, UserProfile, User
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import json

CATEGORIES = ["tech", "sports", "finance", "health"]
N_CLUSTERS = 3

# ─── Seeded content catalogue (fallback when no YouTube API key) ───────────────
SEEDED_CONTENT = {
    "tech": [
        {"content_id": "c001", "title": "Python async explained",       "category": "tech",    "source": "seeded", "url": "https://example.com/c001"},
        {"content_id": "c002", "title": "React hooks deep dive",        "category": "tech",    "source": "seeded", "url": "https://example.com/c002"},
        {"content_id": "c003", "title": "System design for beginners",  "category": "tech",    "source": "seeded", "url": "https://example.com/c003"},
        {"content_id": "c004", "title": "FastAPI full course 2025",     "category": "tech",    "source": "seeded", "url": "https://example.com/c004"},
        {"content_id": "c005", "title": "AWS for developers",           "category": "tech",    "source": "seeded", "url": "https://example.com/c005"},
    ],
    "sports": [
        {"content_id": "c006", "title": "Chelsea vs Arsenal highlights","category": "sports",  "source": "seeded", "url": "https://example.com/c006"},
        {"content_id": "c007", "title": "IPL 2025 match recap",         "category": "sports",  "source": "seeded", "url": "https://example.com/c007"},
        {"content_id": "c008", "title": "NBA playoffs best moments",    "category": "sports",  "source": "seeded", "url": "https://example.com/c008"},
        {"content_id": "c009", "title": "Cricket World Cup analysis",   "category": "sports",  "source": "seeded", "url": "https://example.com/c009"},
        {"content_id": "c010", "title": "F1 2025 season highlights",    "category": "sports",  "source": "seeded", "url": "https://example.com/c010"},
    ],
    "finance": [
        {"content_id": "c011", "title": "How to invest at 22",          "category": "finance", "source": "seeded", "url": "https://example.com/c011"},
        {"content_id": "c012", "title": "Bitcoin market analysis",      "category": "finance", "source": "seeded", "url": "https://example.com/c012"},
        {"content_id": "c013", "title": "Zerodha beginners guide",      "category": "finance", "source": "seeded", "url": "https://example.com/c013"},
        {"content_id": "c014", "title": "Mutual funds explained",       "category": "finance", "source": "seeded", "url": "https://example.com/c014"},
        {"content_id": "c015", "title": "Personal finance in your 20s", "category": "finance", "source": "seeded", "url": "https://example.com/c015"},
    ],
    "health": [
        {"content_id": "c016", "title": "10-minute HIIT workout",       "category": "health",  "source": "seeded", "url": "https://example.com/c016"},
        {"content_id": "c017", "title": "Mediterranean diet guide",     "category": "health",  "source": "seeded", "url": "https://example.com/c017"},
        {"content_id": "c018", "title": "Sleep and productivity",       "category": "health",  "source": "seeded", "url": "https://example.com/c018"},
        {"content_id": "c019", "title": "Mental health for developers", "category": "health",  "source": "seeded", "url": "https://example.com/c019"},
        {"content_id": "c020", "title": "Yoga for beginners",           "category": "health",  "source": "seeded", "url": "https://example.com/c020"},
    ],
}


def get_user_feature_vector(user_id: str, db) -> np.ndarray:
    """Convert a user's behavior logs into a numeric feature vector."""
    logs = db.query(BehaviorLog).filter(BehaviorLog.user_id == user_id).all()
    if not logs:
        return np.zeros(len(CATEGORIES))

    scores = {cat: 0.0 for cat in CATEGORIES}
    now = datetime.utcnow()

    for log in logs:
        if log.category not in scores:
            continue
        age_days = (now - log.created_at).days
        recency_weight = 1 / (1 + age_days * 0.1)
        scores[log.category] += log.value * recency_weight

    return np.array([scores[cat] for cat in CATEGORIES])


def get_all_user_vectors(db) -> tuple:
    """Get feature vectors for ALL users — needed to train K-Means."""
    users = db.query(User).all()
    if len(users) < N_CLUSTERS:
        return [], []

    user_ids, vectors = [], []
    for user in users:
        vec = get_user_feature_vector(user.id, db)
        user_ids.append(user.id)
        vectors.append(vec)

    return user_ids, np.array(vectors)


def train_kmeans(vectors: np.ndarray) -> tuple:
    """Train K-Means clustering on all user vectors."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(vectors)
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    kmeans.fit(scaled)
    return kmeans, scaler


def get_cluster_top_categories(cluster_id: int, all_labels, user_ids: list, db) -> dict:
    """Find what categories users in the same cluster engage with most."""
    same_cluster_user_ids = [
        uid for uid, label in zip(user_ids, all_labels)
        if label == cluster_id
    ]

    cluster_scores = {cat: 0.0 for cat in CATEGORIES}
    for uid in same_cluster_user_ids:
        logs = db.query(BehaviorLog).filter(BehaviorLog.user_id == uid).all()
        for log in logs:
            if log.category in cluster_scores:
                cluster_scores[log.category] += log.value

    total = sum(cluster_scores.values())
    if total == 0:
        return cluster_scores

    return {k: round(v / total, 3) for k, v in cluster_scores.items()}


def hybrid_score(
    personal_scores: dict,
    cluster_scores: dict,
    personal_weight: float = 0.70,
    cluster_weight: float = 0.30
) -> dict:
    """
    Combine personal interest scores (70%) with cluster behavior (30%).
    This is the hybrid engine core.
    """
    all_categories = set(personal_scores) | set(cluster_scores)
    combined = {}

    for cat in all_categories:
        personal = personal_scores.get(cat, 0.0)
        cluster  = cluster_scores.get(cat, 0.0)
        combined[cat] = round(
            (personal * personal_weight) + (cluster * cluster_weight), 3
        )

    # Normalize to sum to 1.0
    total = sum(combined.values())
    if total > 0:
        combined = {k: round(v / total, 3) for k, v in combined.items()}

    return combined


def get_cluster_label(center: np.ndarray) -> str:
    dominant_idx = np.argmax(center)
    labels = {
        0: "Tech Enthusiast",
        1: "Sports Fan",
        2: "Finance Focused",
        3: "Health Conscious"
    }
    return labels.get(dominant_idx, "Mixed Interest")


def build_user_profile(user_id: str):
    db = SessionLocal()
    try:
        # ── Step 1: Personal feature vector ──────────────────────────────
        user_vector = get_user_feature_vector(user_id, db)
        if np.sum(user_vector) == 0:
            print(f"[ML ENGINE] No behavior data for {user_id}")
            return

        total = np.sum(user_vector)
        personal_scores = {
            CATEGORIES[i]: round(float(user_vector[i]) / float(total), 3)
            for i in range(len(CATEGORIES))
        }

        # ── Step 2: K-Means clustering ────────────────────────────────────
        cluster_info = {}
        hybrid_scores = personal_scores.copy()  # default = personal only

        user_ids, all_vectors = get_all_user_vectors(db)

        if len(user_ids) >= N_CLUSTERS:
            kmeans, scaler = train_kmeans(all_vectors)

            user_scaled = scaler.transform(user_vector.reshape(1, -1))
            cluster_id  = int(kmeans.predict(user_scaled)[0])
            all_labels  = kmeans.labels_

            cluster_center = scaler.inverse_transform(
                kmeans.cluster_centers_[cluster_id].reshape(1, -1)
            )[0]
            cluster_label = get_cluster_label(cluster_center)

            # What does this cluster watch?
            cluster_scores = get_cluster_top_categories(
                cluster_id, all_labels, user_ids, db
            )

            # ── Step 3: Hybrid scoring (70% personal + 30% cluster) ──────
            hybrid_scores = hybrid_score(personal_scores, cluster_scores)

            same_cluster = [
                uid for uid, label in zip(user_ids, all_labels)
                if label == cluster_id and uid != user_id
            ]

            cluster_info = {
                "cluster_id":       cluster_id,
                "cluster_label":    cluster_label,
                "cluster_size":     int(np.sum(all_labels == cluster_id)),
                "cluster_scores":   cluster_scores,
                "similar_users":    same_cluster[:5],
            }
            print(f"[ML ENGINE] Hybrid scores for {user_id}: {hybrid_scores}")
        else:
            print(f"[ML ENGINE] {len(user_ids)}/{N_CLUSTERS} users — scoring only")

        # ── Step 4: Build final profile ───────────────────────────────────
        top_interest = max(hybrid_scores, key=hybrid_scores.get)

        profile_data = {
            "personal_scores":  personal_scores,
            "cluster_scores":   cluster_info.get("cluster_scores", {}),
            "hybrid_scores":    hybrid_scores,
            "interest_scores":  hybrid_scores,   # used by recommend/ads/why-this
            "top_interest":     top_interest,
            "feature_vector":   user_vector.tolist(),
            "cluster":          cluster_info,
            "algorithm":        "hybrid_kmeans" if cluster_info else "scoring",
            "weights":          {"personal": 0.70, "cluster": 0.30},
            "updated_at":       datetime.utcnow().isoformat()
        }

        scores_json = json.dumps(profile_data)

        # ── Step 5: Save to DB ────────────────────────────────────────────
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if profile:
            db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).update({
                "interest_scores": scores_json,
                "updated_at":      datetime.utcnow()
            })
        else:
            db.add(UserProfile(
                user_id=user_id,
                interest_scores=scores_json,
                updated_at=datetime.utcnow()
            ))

        db.commit()
        print(f"[ML ENGINE] Profile saved. Top: {top_interest} | Algo: {profile_data['algorithm']}")

    except Exception as e:
        print(f"[ML ENGINE] Error: {e}")
        db.rollback()
    finally:
        db.close()