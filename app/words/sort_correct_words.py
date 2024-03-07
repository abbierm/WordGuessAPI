from correct import correct_words
import os
from pathlib import Path
from math import floor

def merge_sort(words: list[str]) -> list[str]:
    if len(words) == 1 or len(words) == 0:
        return words
    
    mid = floor(len(words) / 2)

    left, right = merge_sort(words[:mid]), merge_sort(words[mid:])

    results = []
    l, r = 0, 0

    while len(results) < len(words):
        if left[l] < right[r]:
            results.append(left[l])
            l += 1
        else:
            results.append(right[r])
            r += 1
        
        if len(left) == l:
            results.extend(right[r:])
            break
        elif len(right) == r:
            results.extend(left[l:])
            break

    return results


sorted_words = merge_sort(correct_words)


this_directory = os.path.dirname(os.path.realpath(__file__))
new_name = 'correct_1.py'
new_file = Path(this_directory, new_name)

with open(new_file, "w") as f:
    f.write('# Acceptable wordle words')
    f.write('\n\n')
    f.write('correct_words = [\n')
    for word in sorted_words:
        f.write('"' + word + '",\n')
    f.write(']')