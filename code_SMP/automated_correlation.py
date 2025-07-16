import numpy as np

def find_reference_profile(similarity_matrix, threshold, labels=None):
    """
    Finds best reference profile
    Selection order:
        1. Max number of neighbors
        2. Highest minimal similarity among neighbors
        3. Highest mean similarity among neighbors

    Parameters:
        similarity_matrix (np.ndarray): square similarity matrix
        threshold (float): similarity threshold
        labels (list): optional profile names

    Returns:
        (reference_index, remaining_indices): index of reference profile,
                                              list of indices of neighbors
    """
    n = similarity_matrix.shape[0]
    M = list(range(n))

    candidates = []

    for i in M:
        sims = [(j, similarity_matrix[i, j]) for j in M if j != i]
        neighbors = [j for j, s in sims if s >= threshold]
        count = len(neighbors)
        if neighbors:
            sims_values = [s for j, s in sims if s >= threshold]
            min_sim = min(sims_values)
            mean_sim = np.mean(sims_values)
        else:
            min_sim = 0.0
            mean_sim = 0.0

        if count > 0:
            candidates.append((i, count, min_sim, mean_sim, neighbors))

    if not candidates:
        return None, []

    # 1. Select by highest count
    max_count = max(c[1] for c in candidates)
    best_candidates = [c for c in candidates if c[1] == max_count]

    if len(best_candidates) == 1:
        best = best_candidates[0]
        return best[0], best[4]

    # 2. Select by highest minimal similarity
    max_min = max(c[2] for c in best_candidates)
    best_min_candidates = [c for c in best_candidates if c[2] == max_min]

    if len(best_min_candidates) == 1:
        best = best_min_candidates[0]
        return best[0], best[4]

    # 3. Select by highest mean similarity
    best = max(best_min_candidates, key=lambda x: x[3])
    return best[0], best[4]


def find_highest_similarity_pairs(similarity_matrix, labels):
    """
    For each profile, find the profile with the highest similarity
    (excluding itself) and build pairs.

    Parameters:
        similarity_matrix (np.ndarray): square similarity matrix
        labels (list): list of profile names (strings)

    Returns:
        pairs (list of tuple): list of unique sorted pairs (label1, label2)
    """
    n = similarity_matrix.shape[0]
    pairs_set = set()

    for i in range(n):
        sims = [(j, similarity_matrix[j, i]) for j in range(n) if j != i]
        j_max, max_sim = max(sims, key=lambda x: x[1])

        # be sure smaller number (=last 4 digits of label) is first profile! 
        if labels[i][-4:] <= labels[j_max][-4:]:
            pair = (labels[i], labels[j_max])
        else:
            pair = (labels[j_max], labels[i])

        if pair not in pairs_set:
            pairs_set.add(pair)

    # Convert set to sorted list
    pairs = sorted(list(pairs_set))
    return pairs


if __name__ == "__main__":
    # Labels for day 1
    labels = [
        "S45M1056", "S45M1057", "S45M1058", "S45M1059", "S45M1060",
        "S45M1061", "S45M1062", "S45M1063", "S45M1064", "S45M1065"
    ]

    # Cosine Similarity Matrix for day 1 
    S = np.array([
        [1.00, 0.91, 0.86, 0.87, 0.81, 0.95, 0.87, 0.91, 0.88, 0.84],
        [0.91, 1.00, 0.82, 0.90, 0.83, 0.90, 0.87, 0.89, 0.87, 0.82],
        [0.86, 0.82, 1.00, 0.82, 0.70, 0.88, 0.82, 0.92, 0.87, 0.83],
        [0.87, 0.90, 0.82, 1.00, 0.84, 0.85, 0.87, 0.85, 0.93, 0.86],
        [0.81, 0.83, 0.70, 0.84, 1.00, 0.79, 0.83, 0.77, 0.81, 0.84],
        [0.95, 0.90, 0.88, 0.85, 0.79, 1.00, 0.87, 0.92, 0.88, 0.81],
        [0.87, 0.87, 0.82, 0.87, 0.83, 0.87, 1.00, 0.81, 0.88, 0.93],
        [0.91, 0.89, 0.92, 0.85, 0.77, 0.92, 0.81, 1.00, 0.85, 0.78],
        [0.88, 0.87, 0.87, 0.93, 0.81, 0.88, 0.88, 0.85, 1.00, 0.90],
        [0.84, 0.82, 0.83, 0.86, 0.84, 0.81, 0.93, 0.78, 0.90, 1.00]
    ])

    #labels for day 2
    labels = [
        "S45M1083", "S45M1084", "S45M1085", "S45M1086", "S45M1087",
        "S45M1089", "S45M1090", "S45M1091", "S45M1092", "S45M1093"
    ]

    # Cosine Similarity Matrix Day 2
    S = np.array([
        [1.00, 0.79, 0.53, 0.75, 0.61, 0.86, 0.59, 0.46, 0.76, 0.62],
        [0.79, 1.00, 0.75, 0.62, 0.68, 0.78, 0.75, 0.56, 0.62, 0.64],
        [0.53, 0.75, 1.00, 0.62, 0.79, 0.59, 0.69, 0.85, 0.62, 0.78],
        [0.75, 0.62, 0.62, 1.00, 0.74, 0.66, 0.64, 0.59, 0.95, 0.82],
        [0.61, 0.68, 0.79, 0.74, 1.00, 0.69, 0.62, 0.73, 0.73, 0.86],
        [0.86, 0.78, 0.59, 0.66, 0.69, 1.00, 0.61, 0.49, 0.67, 0.67],
        [0.59, 0.75, 0.69, 0.64, 0.62, 0.61, 1.00, 0.68, 0.64, 0.68],
        [0.46, 0.56, 0.85, 0.59, 0.73, 0.49, 0.68, 1.00, 0.60, 0.74],
        [0.76, 0.62, 0.62, 0.95, 0.73, 0.67, 0.64, 0.60, 1.00, 0.82],
        [0.62, 0.64, 0.78, 0.82, 0.86, 0.67, 0.68, 0.74, 0.82, 1.00]
    ])

    # good threshold for day 2 , day 1 = 0.85
    threshold = 0.75

    ref_idx, remaining = find_reference_profile(S, threshold, labels)

    if ref_idx is not None:
        print(f"\nSelected reference profile: {labels[ref_idx]}")
        print(f"Remaining profiles: {[labels[i] for i in remaining]}")
    else:
        print("No valid group was found.")

    pairs = find_highest_similarity_pairs(S, labels)

    print("\nUnique pairs:")
    for p in pairs:
        print(p)
