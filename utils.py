import random

# generating all length k string from vocab
def generate_all_k_strings(vocab, k):
    if k == 0:
        return ['']
    if k == 1:
        return vocab
    all_k_strings = []
    for k_string in generate_all_k_strings(vocab, k-1):
        for char in vocab:
            all_k_strings.append(k_string + char)
    return all_k_strings


def translate_input_output_pairs(args, input_output_pairs):
    input_output_pairs_keys = list(input_output_pairs.keys())
    random.shuffle(input_output_pairs_keys)
    input_output_pairs = {key: input_output_pairs[key] for key in input_output_pairs_keys}
    k = args.k
    prompt = """
Below is a list of input-output pairs. Please provide a set of rules that can generate the output from the input.

"""
    for input, output in input_output_pairs.items():
        prompt += f"{input} -> {output}\n"

    prompt += f"""
Think step by step before providing the rules.

Provide a minimum set of rules that can generate the output from the input. 
You don't need to provide trivial rules where input and output are the same, like 'a -> a' or 'ab -> ab'.
Notice that the input of each rule always have length <= {k}. 

Write rules in the following format:
input -> output

Surround rules by XML tags <START> and <END> like below:

<START>
input1 -> output1
input2 -> output2
...
inputn -> outputn
<END>
"""

    return prompt


if __name__ == '__main__':
    vocab = ['a', 'b']
    k = 3
    print(generate_all_k_strings(vocab, k)) # ['aaa', 'aab', 'aba', 'abb', 'baa', 'bab', 'bba', 'bbb']
if __name__ == '__main__':
    vocab = ['a', 'b']
    k = 3
    print(generate_all_k_strings(vocab, k)) # ['aaa', 'aab', 'aba', 'abb', 'baa', 'bab', 'bba', 'bbb']
