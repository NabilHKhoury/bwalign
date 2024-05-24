from affine_alignment import AffineAlignment

def compute_max_seed(ref: str, read: str, seed_idxes: list[list[int]],
                     match_reward: int, mismatch_penalty: int,
                     gap_opening_penalty: int, gap_extension_penalty: int) -> tuple[int, int]:
    """
    For each index in the seeds list, generates an affine alignment (50x50) for each seed index.
    By the end, returns position in ref and score of max scoring alignment. The alignment
    will be between the entire read and a length 50 segment of the reference starting at
    the calculated position.
    """
    best_score = float('-inf')
    best_idx = -1
    for i in range(0, len(seed_idxes)):
        for ref_idx in seed_idxes[i]:
            ref_segment = ref[ref_idx - i:ref_idx - i + 50]
            score, _, _, = AffineAlignment(match_reward, mismatch_penalty, 
                                            gap_opening_penalty, gap_extension_penalty,
                                            ref_segment, read)
            if score > best_score:
                best_score = score
                best_idx = ref_idx
    return best_idx, best_score

def main():
    # still need some more test cases for this to be sure it works as intended.
    ref = 'AATCGGGTTCAATCGGGGTAATCGGGTTCAATCGGGGT'
    read = 'TCGGGTTCAATCGG'
    seed_idxes = [[21, 2], [22, 3], [23, 4], [24, 5], [25, 6], [26, 7], [27, 8]]
    print(compute_max_seed(ref, read, seed_idxes, 1, 5, 2, 1))

if __name__ == '__main__':
    main()