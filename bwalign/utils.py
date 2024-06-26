from Bio import SeqIO
import random
import numpy as np
import sys

"""
    File:          utils.py
    Description:   Script containing all definitions working towards execution of bwalign workflow

    Names:         Adrian Layer, Nabil Khoury, Yasmin A. Jaber
    Emails:        alayer@ucsd.edu, nkhoury@ucsd.edu, yjaber@ucsd.edu
    Project:       bwalign (final project for CSE 185 @ UC San Diego)
    Repository:    https://github.com/NabilHKhoury/bwalign
"""

### CIGAR STRING CREATOR

def calculate_cigar(alignment_s, alignment_t):
    """
    Calculates the cigar string of alignments between strings s and t, inputted
    in the form of alignments of both strings.
    
    args:
        alignment_s (str): the alignment of string s
        alignment_t (str): the alignment of string t
    
    returns:
        cigar string of alignment between s and t
    """
    cigar = []
    match = 0
    ins = 0
    del_ = 0

    for s, t in zip(alignment_s, alignment_t):
        if s == '-' and t != '-':  #del in quer
            if match > 0:
                cigar.append(f"{match}M") 
                match = 0
            del_ += 1
        elif s != '-' and t == '-':  #insertion
            if match > 0:
                cigar.append(f"{match}M")
                match = 0
            ins += 1
        else:  # Match or mismatch
            if ins > 0:
                cigar.append(f"{ins}I")  
                ins = 0
            if del_ > 0:
                cigar.append(f"{del_}D")
                del_ = 0
            match += 1

    if match > 0:
        cigar.append(f"{match}M")
    if ins > 0:
        cigar.append(f"{ins}I")
    if del_ > 0:
        cigar.append(f"{del_}D")

    return ''.join(cigar)

### BANDED ALIGNMENT

def banded_alignment(mr: int, mmp: int, indp: int, bp: int, s: str, t: str) -> float:
    """
    Calculates the maximal banded alignment SCORE between strings s and t given
    alignment parameters.
    
    O(n * m) runtime where n = len(s), m = len(t)
    
    args:
        mr (int): reward for a match between two bases in the alignment
        mmp (int): penalty for a mismtach bewteen two bases in the alignment
        indp (int): penalty for an insertion or deletion in the alignment
        bp (int): band width parameter for alignment
        s (str): first string to be aligned
        t (str): second string to be aligned
        
    returns:
        best alignment score of all alignments between s and t, returns float('-inf')
        if no alignment is possible given the parameters
    """
    l = np.full((len(s)+1,len(t)+1), -np.inf)
    for i in range(0, len(s) + 1):
        for j in range(0, len(t) + 1):
            if i == 0 and j == 0:
                l[i,j] = 0
                continue
            if abs(j-i) < bp:
                if i == 0:
                    l[i,j] = j * (-indp)
                    continue
                if j == 0:
                    l[i,j] = i * (-indp)
                    continue
                match = -mmp
                if s[i-1] == t[j-1]:
                    match = mr
                l[i,j] = max(l[i-1][j] - indp, l[i][j-1] - indp, l[i-1][j-1] + match)
            else:
                continue
    score = l[len(s),len(t)]
    if score > float('-inf'):
        return int(l[len(s),len(t)])
    else:
        return float('-inf')

def BandedAlignmentWithBackTrack(match_reward: int, mismatch_penalty: int, indel_penalty: int,
                    band_parameter: int, s: str, t: str) -> tuple[int, str, str]:
    """
    Calculates the maximal banded alignment SCORE along with the ALIGNMENTS THEMSELVES
    between strings s and t given alignment parameters.
    
    O(n * m) runtime where n = len(s), m = len(t)
    
    args:
        mr (int): reward for a match between two bases in the alignment
        mmp (int): penalty for a mismtach bewteen two bases in the alignment
        indp (int): penalty for an insertion or deletion in the alignment
        bp (int): band width parameter for alignment
        s (str): first string to be aligned
        t (str): second string to be aligned
        
    returns:
        - best alignment score of all alignments between s and t, returns float('-inf')
        if no alignment is possible given the parameters
        - returns the alignment strings of s and t.
    """
    sys.setrecursionlimit(1500)
    l = [[float('-inf')] * (len(t) + 1) for _ in range(len(s) + 1)] # score matrix
    b = [[None] * (len(t)) for _ in range(len(s))] # backtrack matrix
    for i in range(0, len(s) + 1):
        for j in range(0, len(t) + 1):
            if i == 0 and j == 0:
                l[i][j] = 0
            if i == 0:
                l[i][j] = j * (-indel_penalty) # in this case, an empty string s has j indels with t.
                continue
            if j == 0:
                l[i][j] = i * (-indel_penalty)
                continue
            if abs(j-i) < band_parameter:
                match = -mismatch_penalty
                if s[i-1] == t[j-1]:
                    match = match_reward
                l[i][j] = max(l[i-1][j] - indel_penalty, l[i][j-1] - indel_penalty, l[i-1][j-1] + match)
                if l[i][j] == l[i-1][j] - indel_penalty:
                    b[i-1][j-1] = 'd'
                elif l[i][j] == l[i][j-1] - indel_penalty:
                    b[i-1][j-1] = 'r'
                elif l[i][j] == l[i-1][j-1] + match:
                    b[i-1][j-1] = 'dr'
            else:
                continue
    s_align, t_align = backtrack(b, s, t, len(s) - 1, len(t) - 1, band_parameter)
    return l[len(s)][len(t)], s_align, t_align

def backtrack(b: list[list[str]], s: str, t: str, i: int, j: int, band_parameter: int) -> tuple[str, str]:
    """
    Traces alignment using backtracking matrix b from banded alignment in order to
    build the alignments of s and t backwards.
    
    args:
        b (list[list[str]]): backtracking matrix of pointers with (up, down, diag) ptrs
        s (str): first aligned string
        t (str): second aligned string
        i (int): current index in s
        j (int): current index in t
        band_parameter (int): band width parameter for alignment
    """
    if i < 0 and j < 0: # if both i and j reach -1 at the same time, we can just return empty string.
        return '',''
    elif i < 0: # if i reaches -1 first, need to append the rest of t up to index j to t prime, and a number of '-' equal to the length of that string to s prime.
        return '-' * (j + 1), t[0:j+1]
    elif j < 0: # same as i < 0 condition but for j.
        return s[0:i+1], '-' * (i + 1)
    elif b[i][j] == 'd' and abs(j-i) < band_parameter:
        s_prime, t_prime = backtrack(b, s, t, i-1, j, band_parameter)
        return s_prime + s[i], t_prime + '-'
    elif b[i][j] == 'r' and abs(j-i) < band_parameter:
        s_prime, t_prime = backtrack(b, s, t, i, j-1, band_parameter)
        return s_prime + '-', t_prime + t[j]
    else:
        s_prime, t_prime = backtrack(b, s, t, i-1, j-1, band_parameter)
        return s_prime + s[i], t_prime + t[j]

### SEED EXTENSION

def compute_max_seed(ref: str, read: str, seed_idxes: list[list[int]],
                     match_reward: int, mismatch_penalty: int,
                     indel_penalty: int, band_width: int,
                     read_length: int) -> tuple[int, int, str, str]:
    """
    Generates the best scoring seed (based on banded alignment score) of all seeds
    in a seed list of indexes. Returns that seed index, along with the score, and
    the alignments themselves.
    
    args:
        ref (str): reference genome
        read (str): read being aligned to reference
        seed_idxes (list[list[int]]): list of all positions in the genome where each
                                      position in the read found an exact kmer match
        match_reward (int): reward for a match of bases in the banded alignment
        mismatch_penalty (int): penalty for mismatch of bases in alignment
        indel_penalty (int): penalty for insertion or deletion in alignment
        band_width (int): band parameter for alignment
        read_length (int): length of the read being aligned
    """
    if len(seed_idxes) == 0:
        return None
    best_score = float('-inf')
    best_idx = -1
    best_seed = -1
    for i in range(0, len(seed_idxes)):
        for ref_idx in seed_idxes[i]:
            ref_segment = ref[ref_idx - i:ref_idx - i + read_length]
            score = banded_alignment(match_reward, mismatch_penalty, indel_penalty, band_width,
                                            ref_segment, read)
            if score > best_score:
                best_score = score
                best_idx = ref_idx
                best_seed = i
    best_ref_seg = ref[best_idx - best_seed:best_idx - best_seed + read_length]
    _, s_align, t_align = BandedAlignmentWithBackTrack(match_reward, mismatch_penalty, indel_penalty, band_width,
                                                              best_ref_seg, read)
    return best_idx, best_score, s_align, t_align

### SEED GENERATION

# SUFFIX ARRAY CONSTRUCTION

class suffix:
    """
    Class built to store suffix array indices, conserving memory.
    """
    def __init__(self):
        self.index = 0
        self.rank = [0,0]

def get_rank(char: str) -> int:
    """
    Converts the given char to its ascii value, then subtracts 'a' from it to get a
    clean rank value.
    
    args:
        char (str): character to be converted
    
    returns:
        rank of the given char
    """
    return ord(char) - ord('a')

def suffix_array(text: str) -> list[int]:
    """
    Generates the suffix array of a given database string text using O(n(logn)^2)
    time complexity and O(n) space. To improve to O(nlogn), can use radix sort to
    sort the suffix lists. (n = len(text))
    
    Algorithm ripped from:
    https://www.geeksforgeeks.org/suffix-array-set-2-a-nlognlogn-algorithm/
    
    args:
        text (str): text to be processed
    
    returns:
        suffix array of text
    """
    
    # get the intial array of suffixes before starting to loop through and rank them.
    suffixes = [suffix() for _ in range(len(text))]
    
    # initial (k=2) ranking of suffixes
    for i in range(0, len(text)):
        suffixes[i].index = i
        suffixes[i].rank[0] = get_rank(text[i])
        if (i + 1) < len(text):
            suffixes[i].rank[1] = get_rank(text[i+1])
        else:
            suffixes[i].rank[1] = -1
    
    # https://stackoverflow.com/questions/9376384/sort-a-list-of-tuples-depending-on-two-elements
    suffixes = sorted(suffixes, key=lambda element: (element.rank[0], element.rank[1]))
    
    ind = [0] * len(text) # array to keep track of indices while computing ranks
    
    k = 4
    while (k < 2 * len(text)):
         
        # Assigning rank and index 
        # values to first suffix
        rank = 0
        prev_rank = suffixes[0].rank[0]
        suffixes[0].rank[0] = rank
        ind[suffixes[0].index] = 0
 
        # Assigning rank to suffixes
        for i in range(1, len(text)):
             
            # If first rank and next ranks are 
            # same as that of previous suffix in
            # array, assign the same new rank to 
            # this suffix
            if (suffixes[i].rank[0] == prev_rank and
                suffixes[i].rank[1] == suffixes[i - 1].rank[1]):
                prev_rank = suffixes[i].rank[0]
                suffixes[i].rank[0] = rank
                 
            # Otherwise increment rank and assign    
            else:  
                prev_rank = suffixes[i].rank[0]
                rank += 1
                suffixes[i].rank[0] = rank
            ind[suffixes[i].index] = i
 
        # Assign next rank to every suffix
        for i in range(len(text)):
            nextindex = suffixes[i].index + k // 2
            suffixes[i].rank[1] = suffixes[ind[nextindex]].rank[0] if (nextindex < len(text)) else -1
 
        # Sort the suffixes according to
        # first k characters
        suffixes = sorted(suffixes, key = lambda element: (element.rank[0], element.rank[1]))
 
        k *= 2
        
    to_return = []
    for i in range(0, len(text)):
        to_return.append(suffixes[i].index)
        
    return to_return

def partial_suffix_array(sa: list[int], k: int) -> dict[int, int]:
    """
    Generate a partial suffix array for the given text and interval K.
    
    Runs in O(n) w.r.t. suffix array size.
    
    args:
        sa (list[int]): suffix array to be converted
        k (int): partial suffix array parameter for conversion - larger k gives
                 a smaller partial suffix array, but increases runtime in future
                 calculations using the partial suffix array
        
    returns:
        partial suffix array of size depending on k value
    """
    partial = dict()
    for idx in sa:
        if sa[idx] % k == 0:
            partial[idx] = sa[idx]
    return partial

## BWT creation

def bwt_from_suffix_array(text: str, suffix_array: list[int]) -> str:
    """
    Creates a burrows-wheeler transform of a given text using its suffix array.
    
    Runs in O(n).
    
    args:
        text (str): text to be transformed
        suffix_array (list[int]): suffix array of text
    
    returns:
        burrows-wheeler transform of text
    """
    bwt = []
    for idx in suffix_array:
        bwt.append(text[idx-1])
    return ''.join(bwt)

def bwt_psa_out(text: str, k: int) -> tuple[str, dict[int, int]]:
    sa = suffix_array(text)
    bwt = bwt_from_suffix_array(text, sa)
    psa = partial_suffix_array(sa, k)
    return (bwt, psa)

def compute_rank_arr(bwt: str) -> list[int]:
    """
    This function generates the rank of each position in the last column given by the bwt.
    The rank is the number of occurrences of whatever character is at that position, up to
    that position. This can be done in linear time by iterating through the bwt. The ranks
    will be returned in the form of a list of ranks, obviously indices will be in-built.
    
    Runs in O(n), where n is len(bwt)
    
    args:
        bwt (str): burrows-wheeler transform of our string
    
    returns:
        rank array of the burrows wheeler transform
    """
    rank = []
    counts = dict()
    for char in bwt:
        if char not in counts: counts[char] = 0
        counts[char] += 1
        rank.append(counts[char])
    return rank

def compute_first_occurrences(bwt: str) -> dict[str, int]: # the mapping of c in C is the row at which the character c appears in the first column for the first time.
    """
    Generate a dict where each 'character' is mapped to the index in first column where
    these characters first appeared. In other words because the first column is in alphabetical
    order, we can count the ascii code of each character in the last column, then iterate
    from 0 to 255 to get the count of each ascii character in ascending lexicographic order.
    This is done in linear time.
    
    Runs in O(n), where n is len(bwt)
    
    args:
        bwt (str): burrows-wheeler transform of our string
    
    returns:
        first occurrences dict of the burrows wheeler transform
    """
    C = dict()
    counts = [0 for _ in range(256)]
    for char in bwt:
        C[char] = 0
        counts[ord(char)] += 1
    curr_idx = 0
    for i in range(0,256):
        if counts[i] != 0:
            C[chr(i)] = curr_idx
        for _ in range(counts[i]):
            curr_idx += 1
    return C

def compute_checkpoint_arrs(bwt: str) -> dict[int, list[int]]:
    """
    Similar to ranks, but instead the list stored contains the rank of every character up to
    that index, if the index % C is 0. More memory efficient.
    
    Runs in O(n), where n is len(bwt)
    
    args:
        bwt (str): burrows-wheeler transform of our string
    
    returns:
        checkpoint arrays dict of the burrows-wheeler transform
    """
    C = 5
    ranks = dict()
    rank = [0 for _ in range(256)]
    for i in range(0, len(bwt)):
        rank[ord(bwt[i])] += 1
        if i % C == 0:
            ranks[i] = rank[:]
    return ranks

def compute_rank(bwt: str, idx: int, ranks: dict[int, list[int]], symbol: str, C: int) -> int: # idx can be either top or bot
    """
    Computes the rank of a given symbol within the burrows-wheeler transform using
    auxiliary data structures. In this case, we are not to confuse rank with the
    previously defined rank array. In this case, rank for a symbol L(j) at position
    j in string L as the number of occurrences of the character L(j) that occur in
    positions up to and including j. This technique uses the pre-computed checkpoint
    arrays, now referred to as RANKS.
    
    Runs in O(1).
    
    args:
        bwt (str): burrows-wheeler transform of string
        idx (int): index of character symbol
        ranks (dict[int, list[int]]): pre-computed rank (checkpoint) arrays
        symbol (str): character we are attempting to rank
        C (int): constant defined for both partial suffix array and checkpoint arrays
    
    returns:
        rank of character symbol
    """
    idx_dist_from_chkpnt = idx % C
    idx_rank = ranks[idx - idx_dist_from_chkpnt][ord(symbol)]
    for j in range(idx - idx_dist_from_chkpnt + 1, idx + 1):
        if bwt[j] == symbol:
            idx_rank += 1
    return idx_rank

def bw_better_match_pattern(bwt: str, pattern: str, first_occurrences: dict[str,int], ranks: list[list[int]]) -> tuple[int,int]:
    """
    Matches a pattern and finds a range of its possible indices in last col of bwt using 
    auxiliary data structures that we have precomputed
    
    Runs in O(|pattern|)
    
    args:
        bwt (str): burrows-wheeler transform of text
        pattern (str): pattern we are matching to text
        first_occurrences (dict[str,int]): first-occurences pre-computed data structure
        ranks: pre-computed ranks data structure
    
    returns:
        a range of indices in last col of bwt where the pattern could match in text
    """
    C = 5
    top = 0
    bot = len(bwt) - 1
    for i in range(len(pattern) - 1, -1, -1):
        symbol = pattern[i]
        if symbol not in first_occurrences: # in the case the symbol is not in text at all
            return (0,0)
        top_rank = compute_rank(bwt, top, ranks, symbol, C) # use checkpoint arrs to get the rank
        bot_rank = compute_rank(bwt, bot, ranks, symbol, C)
        marker = False
        if bwt[top] == symbol:
            marker = True
        top = first_occurrences[symbol] + top_rank
        if marker:
            top -= 1
        bot = first_occurrences[symbol] + bot_rank - 1
        if bot - top < 0:
            return (0,0)
    return (top, bot + 1)

def compute_idxes_from_top_bot(start: int, end: int, partial_s_array: dict[int, int], bwt: str, rank: list[int], occurrences: list[int]) -> list[int]:
    """
    Uses the start and end indices we have computed to calculate a list of exact
    indices where the pattern matches in text
    
    Runs in O(|pattern|)
    
    args:
        start (int): starting index in last col of bwt where matches can occur
        end (int): ending index in last col of bwt where matches can occur
        partial_s_array (dict[int, int]): partial suffix array of text
        bwt (str): burrows-wheeler transform of text
        rank (list[int]): rank array given by compute_rank_array function
        occurrences (list[int]): pre-computed first occurrences array
    
    returns:
        list of all indices where the pattern matches in text
    """
    pattern_idxes = []
    for i in range(start, end):
        p = i
        plus_count = 0
        while True:
            predecessor = bwt[p]
            p = occurrences[predecessor] + rank[p] - 1
            plus_count += 1
            if p in iter(partial_s_array.keys()):
                break
        pattern_idxes.append((partial_s_array[p] + plus_count) % len(bwt))
    return pattern_idxes

def generate_seeds(read: str, bwt: str, k: int, psa: dict[int, int],
                                                first_occurrences: dict[str, int],
                                                checkpoint_arrs: dict[int, list[int]],
                                                ranks: list[int]) -> list[list[int]]:
    """
    Takes a read and bwt created from reference genome, and generates a list of lists
    with each index being an index i in the read from 0 to len(read) - k + 1. The corresponding list at each
    index is a list of exact match indices of the kmer at read[i:i+k] located in the reference
    genome. Note that even if two kmers are identical, their indices in the read are not.
    
    Runs in O(m), where m = len(read)
    
    args:
        read (str): read being processed for seeds
        bwt (str): burrows-wheeler transform of reference genome
        k (int): seed length parameter
        psa (dict[int,int]): partial suffix array of reference genome
        first_occurrences (dict[str, int]): first occurrences array of bwt
        checkpoints_arrs (dict[int, list[int]]): checkpoint arrays of bwt
        ranks (list[int]): rank arrays of bwt
        
    returns:
        a list of lists containing exact match indices for the read in reference
    """
    seed_idxes = []
    for i in range(0, len(read) - k + 1):
        kmer = read[i:i+k]
        start, end = bw_better_match_pattern(bwt, kmer, first_occurrences, checkpoint_arrs)
        idxes = compute_idxes_from_top_bot(start, end, psa, bwt, ranks, first_occurrences)
        seed_idxes.append(idxes)
    return seed_idxes

### FASTQ PARSING

def parse_fastq(fastq_path: str) -> list[tuple[str, str, list[int]]]:
    """
    Parse a FASTQ file and return a list of tuples where each tuple contains the
    sequence ID, the sequence itself, and the quality scores.
    
    :param fastq_path: Path to the FASTQ file
    :return: A list of tuples where each tuple contains the sequence ID, the sequence itself, and the quality scores
    """
    fastq_list = []
    with open(fastq_path, "r") as handle:
        for record in SeqIO.parse(handle, "fastq"):
            fastq_list.append((record.id, str(record.seq), record.letter_annotations["phred_quality"]))
    return fastq_list

def parse_reference_genome(fasta_path: str) -> tuple[str, str]:
    """
    Parse a FASTA file containing a reference genome and return a tuple containing
    the sequence ID and the sequence itself.

    :param fasta_path: Path to the FASTA file
    :return: A tuple containing the sequence ID and the sequence itself
    """
    with open(fasta_path, "r") as handle:
        for record in SeqIO.parse(handle, "fasta"):
            return record.id, str(record.seq)

def random_sequence(length: int) -> str:
    """
    Generate a random DNA sequence of the specified length.

    :param length: The length of the sequence
    :return: A random DNA sequence
    """
    return ''.join(random.choices('ACGT', k=length))

def random_quality_scores(length: int) -> list[int]:
    """
    Generate random quality scores for a sequence of the specified length.

    :param length: The length of the sequence
    :return: A list of random quality scores
    """
    return ''.join(random.choices('!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHI', k=length))

def random_id(length: int) -> str:
    """
    Generate a random sequence ID of the specified length.

    :param length: The length of the sequence ID
    :return: A random sequence ID
    """
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))

def generate_fasta_file(fasta_path: str, sequence_id: str, sequence: str):
    """
    Generate a FASTA file with the specified sequence ID and sequence.

    :param fasta_path: Path to the FASTA file to be generated
    :param sequence_id: The sequence ID
    :param sequence: The sequence
    """
    with open(fasta_path, "w") as handle:
        handle.write(f">{sequence_id}\n")
        handle.write(sequence)

def generate_fastq_file(file, read_id, sequence, quality):
    """
    Append a read to the FASTQ file.
    """
    file.write(f"@{read_id}\n")
    file.write(sequence + "\n")
    file.write("+\n")
    file.write(quality + "\n")

def main():
    """
    Used to generate random data for testing
    """
    # Define parameters for random sequence and quality scores
    sequence_length = 100000
    sequence_id_length = 10

    # Generate random reference genome
    ref_sequence_id = random_id(sequence_id_length)
    ref_sequence = random_sequence(sequence_length)
    generate_fasta_file(r"C:\Users\Nabil\Desktop\School\Spring2024\CSE185 - Bioinfo Lab\project\bwalign\data\random_reference.fasta", ref_sequence_id, ref_sequence)

    # Parameters for FASTQ reads
    sequence_length = 50
    num_reads = 10
    fastq_filename = r"C:\Users\Nabil\Desktop\School\Spring2024\CSE185 - Bioinfo Lab\project\bwalign\data\random_reads.fastq"

    # Generate random FASTQ reads and write to a single file
    with open(fastq_filename, 'w') as file:
        for i in range(num_reads):
            read_id = random_id(sequence_id_length)
            read_sequence = random_sequence(sequence_length)
            read_quality = random_quality_scores(sequence_length)
            generate_fastq_file(file, read_id, read_sequence, read_quality)

if  __name__ == '__main__':
    main()
