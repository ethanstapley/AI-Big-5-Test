import json

USER_RESULTS_FILE = "user_results.json"
PERCENTILE_TABLE_FILE = "percentile_lookup_table.json"
OUTPUT_REPORT_FILE = "user_percentile.json"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def compute_trait_scores(user_results):
    trait_scores = {}
    for q_id, entry in user_results.items():
        trait = entry["trait"]
        score = entry["score"]
        trait_scores.setdefault(trait, 0)
        trait_scores[trait] += score
    return trait_scores

def get_percentiles(trait_scores, percentile_table):
    trait_percentiles = {}
    for trait, total_score in trait_scores.items():
        score_key = str(int(round(total_score)))
        percentile = percentile_table[trait].get(score_key, None)
        trait_percentiles[trait] = {
            "score": total_score,
            "percentile": percentile
        }
    return trait_percentiles

def generate_user_report(user_results=None):
    if user_results is None:
        user_results = load_json(USER_RESULTS_FILE)

    percentile_table = load_json(PERCENTILE_TABLE_FILE)

    trait_scores = compute_trait_scores(user_results)
    user_report = get_percentiles(trait_scores, percentile_table)

    with open(OUTPUT_REPORT_FILE, "w") as f:
        json.dump(user_report, f, indent=2)

    return user_report

if __name__ == "__main__":
    report = generate_user_report()
    for trait, info in report.items():
        print(f"{trait}: {info['score']}/30 → {info['percentile']}th percentile")
    print(f"\n Report saved to: {OUTPUT_REPORT_FILE}")
