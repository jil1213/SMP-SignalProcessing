import numpy as np

from pathlib import Path

from a_automated_processing import load_profiles
from b_automated_similarity import compute_aligned_similarity_matrix

def find_reference_profile(similarity_matrix, threshold, labels):
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
        (reference_index, remaining_indices, mean_score): index of reference profile,
                                              list of indices of neighbors, mean of similarity scores
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
        return None, [], 0.0

    # 1. Select by highest count
    max_count = max(c[1] for c in candidates)
    best_candidates = [c for c in candidates if c[1] == max_count]

    # 2. Select by highest minimal similarity
    if len(best_candidates) > 1:
        max_min = max(c[2] for c in best_candidates)
        best_candidates = [c for c in best_candidates if c[2] == max_min]

    # 3. Select by highest mean similarity
    best = max(best_candidates, key=lambda x: x[3])
    ref_idx, _, _, mean_sim, neighbor_indices = best

    ref_label = labels[ref_idx]
    neighbor_labels = [labels[i] for i in neighbor_indices]

    return ref_label, neighbor_labels, mean_sim


def find_highest_similarity_pairs(similarity_matrix, labels):
    """
    For each profile, find the profile with the highest similarity
    (excluding itself) and build pairs.

    Parameters:
        similarity_matrix (np.ndarray): square similarity matrix
        labels (list): list of profile names (strings)

    Returns:
        pairs (list of tuple): list of unique sorted pairs with similarity
                               (label1, label2, similarity)
    """
    n = similarity_matrix.shape[0]
    pairs_dict = {}

    for i in range(n):
        sims = [(j, similarity_matrix[j, i]) for j in range(n) if j != i]
        j_max, max_sim = max(sims, key=lambda x: x[1])

        # be sure smaller number (=last 4 digits of label) is first profile! 
        if labels[i][-4:] <= labels[j_max][-4:]:
            pair = (labels[i], labels[j_max])
        else:
            pair = (labels[j_max], labels[i])

        # if not already added, add with score
        if pair not in pairs_dict:
            pairs_dict[pair] = max_sim

    # convert dict to sorted list of tuples
    pairs = sorted([(a, b, score) for (a, b), score in pairs_dict.items()])
    return pairs


def find_all_threshold_groups(similarity_matrix, labels, threshold):
    """
    For each profile, build a group by adding all profiles with similarity ≥ threshold
    to all current group members

    Parameters:
        similarity_matrix (np.ndarray): square similarity matrix
        labels (list of str): profile names
        threshold (float): similarity threshold

    Returns:
        list of dict: groups with labels and submatrix
    """
    n = similarity_matrix.shape[0]
    all_groups = []

    for i in range(n):

        current_group = [i]

        for j in range(n):
            if j == i:
                continue
            all_above = True
            for k in current_group:
                sim = similarity_matrix[j, k] 
                if sim < threshold: # Below threshold-> candidate rejected
                    all_above = False
                    break
            if all_above:
                current_group.append(j) #else candidate accepted

        if len(current_group) > 1:
            group_labels = sorted([labels[idx] for idx in current_group])
            # Check if same label combination already saved
            if not any(set(group_labels) == set(g['labels']) for g in all_groups):
                # Extract submatrix
                idx_sorted = [labels.index(l) for l in group_labels]
                submatrix = similarity_matrix[np.ix_(idx_sorted, idx_sorted)]
                all_groups.append({
                    "labels": group_labels,
                    "matrix": submatrix
                })

    return all_groups


def analyze_day(folder_path, threshold_override=None):
    """
    Analyze a measurement day by computing similarity, reference, pairs, and groups.

    Returns:
        dict with:
            - day (str)
            - smp_profiles (dict)
            - similarity_matrix (np.ndarray)
            - labels (list)
            - threshold (float)
            - reference_result (tuple): (ref_name, remaining, mean_score)
            - pairs (list): [(a, b, score)]
            - groups (list): list of group dicts {'labels': [...], 'matrix': ...}
    """
    day = folder_path.name
    smp_profiles = load_profiles(folder_path)

    # calculate Similarity matrix S and labels
    corr_df = compute_aligned_similarity_matrix(smp_profiles, day)
    S = corr_df.values
    labels = corr_df.index.tolist()

    threshold = threshold_override if threshold_override is not None else (
        0.85 if day in ['20250131', '20250403', '20191229'] else 0.75)

    ref_result = find_reference_profile(S, threshold, labels)
    pairs = find_highest_similarity_pairs(S, labels)
    groups = find_all_threshold_groups(S, labels, threshold)

    return {
        "day": day,
        "smp_profiles": smp_profiles,
        "similarity_matrix": S,
        "labels": labels,
        "threshold": threshold,
        "reference_result": ref_result,
        "pairs": pairs,
        "groups": groups}


if __name__ == "__main__":

    root = Path(__file__).resolve().parent 
    input_root = root/ "raw_data"
    output_dir = root / "output" / "groups"
    output_dir.mkdir(parents=True, exist_ok=True)

    for folder_path in sorted(input_root.iterdir()):
        if folder_path.is_dir():
            result = analyze_day(folder_path)

            day = result["day"]
            smp_profiles = result["smp_profiles"]
            S = result["similarity_matrix"]
            labels = result["labels"]
            threshold = result["threshold"]
            ref_result = result["reference_result"]
            pairs = result["pairs"]
            groups = result["groups"]

            output_file = output_dir / f"groups_{day}.txt"

            with output_file.open("w") as f:
                ref_name, remaining, mean_score = ref_result

                if ref_name is not None:
                    f.write(f"Selected reference profile: {ref_name}\n")
                    f.write(f"Remaining profiles: {remaining}\n")
                    f.write(f"Mean similarity score: {mean_score:.4f}\n\n")
                else:
                    f.write("No valid group was found.\n\n")

                # highest similarity pairs
                f.write("Unique pairs with scores:\n")
                for a, b, score in pairs:
                        f.write(f"{a} - {b}: Similarity = {score:.4f}\n")

                # threshold groups
                f.write("\nGroups ready for further processing:\n")
                for idx, g in enumerate(groups, 1):
                    f.write(f"\nGroup {idx}: {g['labels']}\n")
                    f.write(f"{g['matrix']}\n")

                    # reference in each group
                    group_ref_name, group_remaining, group_mean_score = find_reference_profile(
                      g["matrix"], threshold, labels=g["labels"])
                    if ref_name is not None:
                        f.write(f"\nSelected reference profile: {group_ref_name}\n")
                        f.write(f"Remaining profiles: {group_remaining}\n")
                        f.write(f"Mean similarity score: {group_mean_score:.4f}\n")