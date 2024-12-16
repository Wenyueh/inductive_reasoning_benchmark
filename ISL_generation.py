import argparse
import random
import time
import config
from utils import generate_all_k_strings, translate_input_output_pairs

# generating rules
def generate_rules(args):
    def one_batch_generating_rules(args, number_of_rules):
        all_k_strings = ['']*number_of_rules
        for _ in range(args.k):
            for i in range(number_of_rules):
                all_k_strings[i] += random.choice(config.vocab)

        random_k_all_k_strings = []
        for all_k_string in all_k_strings:
            length = random.randint(2, args.k)
            truncated_string = all_k_string[:length]
            is_suffix = False
            for s in random_k_all_k_strings:
                if truncated_string == s[-len(truncated_string):] or truncated_string[-len(s):] == s:
                    is_suffix = True
            if not is_suffix:
                random_k_all_k_strings.append(truncated_string)

        all_k_strings = random_k_all_k_strings
        return all_k_strings
    
    rules = {}
    all_k_strings = []
    while len(all_k_strings) < args.number_of_rules:
        number_of_rules = args.number_of_rules - len(all_k_strings)
        new_rules = one_batch_generating_rules(args, number_of_rules)
        all_k_strings += new_rules
        all_k_strings = list(set(all_k_strings))

    # if all k strings are not of length k
    # add random characters to make one of them to be of length k
    if max([len(k_string) for k_string in all_k_strings]) < args.k:
        all_k_strings[-1] = ''.join([random.choice(config.vocab) for _ in range(args.k - len(all_k_strings[-1]))]) + all_k_strings[-1] 

    for k_string in all_k_strings:
        possible_output = list(set(config.vocab).difference([k_string[-1]])) + [''] # allow deletion
        rules[k_string] = random.choice(possible_output)

    return rules

# generate sample dataset
# S1 = {(w, w0) | [w ∈ Σ≤k ∧ f(w) = w0]}
# sample size: Sum_1^k vocab^i = vocab^1 + vocab^2 + ... + vocab^k
def generate_sample_dataset(rules):
    sample = {}
    for k in range(1, args.k+1):
        one_sample_inputs = generate_all_k_strings(config.vocab, k)
        for input in one_sample_inputs:
            output = apply_rule(args, rules, input)
            sample[input] = output
    return sample


# generate size n dataset containing the sample dataset
def generate_fixed_size_dataset(rules, n):
    sample_dataset = generate_sample_dataset(rules)
    assert n >= len(sample_dataset)
    extra_datapoints_number = n - len(sample_dataset)
    n= 0
    while n < extra_datapoints_number:
        length = random.randint(1, 3*args.k)
        datapoint = ''.join([random.choice(config.vocab) for _ in range(length)])
        if datapoint not in rules:
            input = datapoint
            output = apply_rule(args, rules, input)
            sample_dataset[input] = output
            n += 1
    return sample_dataset

# rule application
def apply_rule(args, rules, input):
    output = ''
    for i in range(len(input)):
        # go through all k
        modified = False
        for k in range(1, args.k+1):
            suffix = input[:i+1][-k:]     
            if suffix in rules:
                output += rules[suffix]
                modified = True
                break
        if not modified:
            output += input[i]
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate ISLs')
    parser.add_argument('--k', type=int, default=2, help='number of k in ISL_k')
    parser.add_argument('--vocab_size', type=int, default=2, help='number of vocab in ISL_k')
    parser.add_argument('--number_of_rules', type=int, default=2, help='number of rules in ISL_k, must be smaller than vocab_size^k')
    args = parser.parse_args()

    random.seed(0)

    # Check if number_of_rules is smaller than vocab_size^k
    if args.number_of_rules > args.vocab_size**args.k:
        raise ValueError('number_of_rules must be smaller than vocab_size^k')

    # Generate vocab
    config.vocab = list('abcdefghijklmnopqrstuvwxyz'[:args.vocab_size])

    # Generate rules
    rules = generate_rules(args)
    print(rules)
    print("=====================================")

    # Generate sample dataset
    sample_dataset = generate_sample_dataset(rules)
    sample_dataset = generate_fixed_size_dataset(rules, 2*len(sample_dataset))

    prompt = translate_input_output_pairs(args, sample_dataset)
    print(prompt)
